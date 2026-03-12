#!/usr/bin/env python3
"""Quick DB state checker for iteration 52 fixes"""
import asyncio
import motor.motor_asyncio
import os
import sys
sys.path.insert(0, '/app/backend')
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME', 'free11')

async def check():
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Check seed users
    seed_users = await db.users.find(
        {'is_seed': True},
        {'_id': 0, 'name': 1, 'is_seed': 1, 'is_admin': 1}
    ).to_list(20)
    print('SEED USERS:', seed_users)
    
    # Check admin users
    admin_users = await db.users.find(
        {'is_admin': True},
        {'_id': 0, 'name': 1, 'is_seed': 1, 'is_admin': 1}
    ).to_list(20)
    print('ADMIN USERS:', admin_users)
    
    # Check products with Butter
    import re
    butter = await db.products.find(
        {'name': {'$regex': 'Butter', '$options': 'i'}},
        {'_id': 0, 'name': 1, 'brand': 1}
    ).to_list(10)
    print('BUTTER PRODUCTS:', butter)
    
    # Check products with Amul
    amul = await db.products.find(
        {'name': {'$regex': 'Amul', '$options': 'i'}},
        {'_id': 0, 'name': 1, 'brand': 1}
    ).to_list(10)
    print('AMUL PRODUCTS:', amul)
    
    # Check total users
    total = await db.users.count_documents({})
    print(f'TOTAL USERS: {total}')

asyncio.run(check())
