import json
import re
from typing import Dict, Any, Optional
from datetime import datetime
import pandas as pd
from sqlalchemy.orm import Session
from fastapi import HTTPException
import google.generativeai as genai
import models
import schemas
import utils
from app.core.config import settings
from app.services.transaction_pipeline import TransactionPipeline, IngestionItem

class ReceiptOCRService:
    def __init__(self, db: Session):
        self.db = db
        self.pipeline = TransactionPipeline(db)

    def extract_receipt(self, file_bytes: bytes, mime_type: str) -> Dict[str, Any]:
        """Extract structured fields from receipt image with graceful fallback."""
        if not settings.GEMINI_API_KEY:
            return {
                "merchant": "Receipt Merchant",
                "total": 0.0,
                "amount": 0.0,
                "category": "other",
                "date": datetime.utcnow().strftime("%Y-%m-%d"),
                "tax": 0.0,
                "items": [],
                "payment_method": "Unknown",
                "confidence": 0.3,
                "description": "Scanned receipt (offline fallback)"
            }

        try:
            from app.ai.providers import get_vision_provider
            vision_provider = get_vision_provider()

            prompt = """
Analyze this receipt image. Extract all details and return ONLY a strict JSON object with these keys:
- merchant: string (merchant or store name)
- total: float (final total amount paid)
- amount: float (same as total)
- category: string (one of: food, transportation, entertainment, utilities, healthcare, shopping, housing, other)
- date: string (YYYY-MM-DD or empty string)
- tax: float (tax amount or 0.0)
- items: list of objects with keys "name" and "price"
- payment_method: string (e.g. Visa, Mastercard, Cash, UPI, Apple Pay, Unknown)
- confidence: float (between 0.1 and 1.0 based on image legibility)
- description: string (summary description e.g. "Lunch at Starbucks")
"""
            raw_text = vision_provider.extract_from_image(prompt, file_bytes, mime_type)
            raw_text = raw_text.strip()
            raw_text = re.sub(r"```json\s*|\s*```", "", raw_text).strip()
            data = json.loads(raw_text)

            # Sanitize and assign defaults
            data["amount"] = float(data.get("amount") or data.get("total") or 0.0)
            data["total"] = data["amount"]
            data["merchant"] = str(data.get("merchant") or "Unknown Store")
            data["confidence"] = float(data.get("confidence") or 0.85)
            data["category"] = str(data.get("category") or "other").lower()
            return data
        except Exception as err:
            return {
                "merchant": "Receipt Merchant",
                "total": 0.0,
                "amount": 0.0,
                "category": "other",
                "date": datetime.utcnow().strftime("%Y-%m-%d"),
                "tax": 0.0,
                "items": [],
                "payment_method": "Unknown",
                "confidence": 0.2,
                "description": f"Scanned receipt (OCR error: {str(err)})"
            }

    def stage_receipt(self, user_id: int, extracted_data: Dict[str, Any]) -> models.ReceiptPending:
        pending = models.ReceiptPending(
            user_id=user_id,
            extracted_data=json.dumps(extracted_data),
            status="pending"
        )
        self.db.add(pending)
        self.db.commit()
        self.db.refresh(pending)
        return pending

    def confirm_receipt(
        self,
        receipt_id: int,
        user: models.User,
        confirm_req: schemas.ReceiptConfirmRequest
    ) -> Optional[models.Transaction]:
        pending = self.db.query(models.ReceiptPending).filter(
            models.ReceiptPending.receipt_id == receipt_id,
            models.ReceiptPending.user_id == user.user_id
        ).first()

        if not pending:
            raise HTTPException(status_code=404, detail="Receipt not found")

        if not confirm_req.confirmed:
            pending.status = "rejected"
            self.db.commit()
            return None

        extracted = json.loads(pending.extracted_data or "{}")
        amount = float(confirm_req.amount or extracted.get("amount") or extracted.get("total") or 0.0)
        category = confirm_req.category or extracted.get("category") or "other"
        desc = confirm_req.description or extracted.get("description") or f"Receipt: {extracted.get('merchant', 'Store')}"
        
        date_val = None
        req_date = getattr(confirm_req, "date", None)
        if req_date:
            date_val = req_date
        elif extracted.get("date"):
            try:
                date_val = pd.to_datetime(extracted["date"]).to_pydatetime()
            except Exception:
                date_val = datetime.utcnow()
        else:
            date_val = datetime.utcnow()

        # Ingest via pipeline
        res = self.pipeline.process_item(
            user=user,
            item=IngestionItem(
                amount=amount,
                description=desc,
                date=date_val,
                category=category,
                source="receipt",
                merchant=extracted.get("merchant"),
                tax=extracted.get("tax"),
                confidence=extracted.get("confidence", 1.0)
            ),
            allow_duplicates=True
        )

        pending.status = "confirmed"
        self.db.commit()
        return res.transaction
