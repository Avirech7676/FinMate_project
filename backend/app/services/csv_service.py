import io
import re
from typing import Dict, Any, List, Optional
import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile
import models
import utils
from app.services.transaction_pipeline import TransactionPipeline, IngestionItem

class CSVImportService:
    def __init__(self, db: Session):
        self.db = db
        self.pipeline = TransactionPipeline(db)

    @staticmethod
    def decode_csv_content(content: bytes) -> str:
        for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
            try:
                return content.decode(enc)
            except Exception:
                continue
        raise HTTPException(status_code=400, detail="Could not decode CSV file.")

    @staticmethod
    def detect_delimiter(sample: str) -> str:
        if sample.count(";") > sample.count(",") and sample.count(";") >= 3:
            return ";"
        elif sample.count("\t") > sample.count(",") and sample.count("\t") >= 3:
            return "\t"
        return ","

    def preview_csv(self, content: bytes) -> Dict[str, Any]:
        text = self.decode_csv_content(content)
        delim = self.detect_delimiter(text[:5000])

        df = pd.read_csv(
            io.StringIO(text),
            sep=delim,
            dtype=str,
            keep_default_na=False,
            engine="python",
        )

        colmap = {utils.normalize_header(c): c for c in df.columns}
        date_col = utils.pick_first(colmap, [
            "date", "transaction date", "posted date", "value date", "txn date", "trans date", "booking date", "time"
        ])
        desc_col = utils.pick_first(colmap, [
            "description", "narration", "details", "transaction details", "particulars", "merchant", "name", "remarks"
        ])
        amt_col = utils.pick_first(colmap, ["amount", "txn amount", "transaction amount", "total", "net amount"])
        cat_col = utils.pick_first(colmap, ["category", "expense category", "type", "tag"])

        samples: List[Dict[str, Any]] = []
        for _, row in df.head(5).iterrows():
            d_val = row.get(date_col, "") if date_col else ""
            desc_val = row.get(desc_col, "") if desc_col else ""
            raw_amt = row.get(amt_col, "") if amt_col else ""
            cat_val = row.get(cat_col, "") if cat_col else ""
            parsed_amt = utils.parse_money(raw_amt) or 0.0
            sugg_cat = utils.suggest_category(desc_val) if not cat_val else cat_val
            samples.append({
                "date": str(d_val),
                "description": str(desc_val),
                "amount": float(parsed_amt),
                "category": sugg_cat
            })

        return {
            "total_rows": len(df),
            "columns": list(df.columns),
            "detected_columns": {
                "date": date_col,
                "description": desc_col,
                "amount": amt_col,
                "category": cat_col
            },
            "sample_rows": samples
        }

    def import_csv_data(
        self,
        content: bytes,
        user: models.User,
        source_currency: Optional[str] = None
    ) -> Dict[str, Any]:
        text = self.decode_csv_content(content)
        delim = self.detect_delimiter(text[:5000])

        df = pd.read_csv(
            io.StringIO(text),
            sep=delim,
            dtype=str,
            keep_default_na=False,
            engine="python",
        )

        colmap = {utils.normalize_header(c): c for c in df.columns}
        date_col = utils.pick_first(colmap, [
            "date", "transaction date", "posted date", "value date", "txn date", "trans date", "booking date", "time"
        ])
        desc_col = utils.pick_first(colmap, [
            "description", "narration", "details", "transaction details", "particulars", "merchant", "name", "remarks"
        ])
        amt_col = utils.pick_first(colmap, ["amount", "txn amount", "transaction amount", "total", "net amount"])
        cat_col = utils.pick_first(colmap, ["category", "expense category", "type", "tag"])

        items: List[IngestionItem] = []
        for _, row in df.iterrows():
            raw_amt = row.get(amt_col) if amt_col else None
            amount = utils.parse_money(raw_amt) if raw_amt is not None else None
            if amount is None or amount == 0:
                continue

            desc = str(row.get(desc_col, "Imported transaction")) if desc_col else "Imported transaction"
            raw_date = row.get(date_col) if date_col else None
            date_dt = None
            if raw_date:
                try:
                    date_dt = pd.to_datetime(raw_date, errors="coerce").to_pydatetime()
                except Exception:
                    date_dt = None

            raw_cat = str(row.get(cat_col, "")) if cat_col else None
            items.append(IngestionItem(
                amount=abs(amount),
                description=desc,
                date=date_dt,
                category=raw_cat,
                source="import"
            ))

        result = self.pipeline.process_batch(user, items, allow_duplicates=False)
        return {
            "status": "success",
            "imported": result["imported_count"],
            "duplicates_skipped": result["duplicates_skipped"],
            "message": f"Successfully imported {result['imported_count']} transactions ({result['duplicates_skipped']} duplicates skipped).",
            "detected_currency": source_currency or user.currency
        }
