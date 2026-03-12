#!/usr/bin/env python3
"""Fix: Tag lb_seed_5 (Match Oracle) with is_seed=True in MongoDB"""
import asyncio
import motor.motor_asyncio
import os
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME', 'free11')

async def fix():
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Tag all lb_seed_* users with is_seed=True
    result = await db.users.update_many(
        {'id': {'$regex': '^lb_seed_'}},
        {'$set': {'is_seed': True}}
    )
    print(f'Updated {result.modified_count} users with is_seed=True')
    
    # Verify
    lb_seed_users = await db.users.find(
        {'id': {'$regex': '^lb_seed_'}},
        {'_id': 0, 'id': 1, 'name': 1, 'is_seed': 1}
    ).to_list(20)
    print('lb_seed users after fix:', lb_seed_users)

asyncio.run(fix())
