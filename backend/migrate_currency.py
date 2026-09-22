#!/usr/bin/env python3
"""
Migration script to add currency fields to existing users
Run this once to update existing database
"""

import sqlite3
import os

def migrate_currency_fields():
    db_path = "finmate.db"
    
    if not os.path.exists(db_path):
        print("Database not found. No migration needed.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if currency columns already exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'currency' not in columns:
            print("Adding currency column...")
            cursor.execute("ALTER TABLE users ADD COLUMN currency TEXT DEFAULT 'USD'")
        
        if 'currency_symbol' not in columns:
            print("Adding currency_symbol column...")
            cursor.execute("ALTER TABLE users ADD COLUMN currency_symbol TEXT DEFAULT '$'")
        
        # Update existing users with default values
        cursor.execute("UPDATE users SET currency = 'USD' WHERE currency IS NULL")
        cursor.execute("UPDATE users SET currency_symbol = '$' WHERE currency_symbol IS NULL")
        
        conn.commit()
        print("✅ Currency migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_currency_fields()