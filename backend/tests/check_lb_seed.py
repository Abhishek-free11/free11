#!/usr/bin/env python3
"""Check lb_seed users in DB"""
import asyncio
import motor.motor_asyncio
import os
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME', 'free11')

async def check():
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Check Match Oracle user
    match_oracle = await db.users.find_one(
        {'name': 'Match Oracle'},
        {'_id': 0, 'id': 1, 'name': 1, 'is_seed': 1, 'is_admin': 1, 'total_earned': 1}
    )
    print('Match Oracle user:', match_oracle)
    
    # Check lb_seed users
    lb_seed_users = await db.users.find(
        {'id': {'$regex': 'lb_seed'}},
        {'_id': 0, 'id': 1, 'name': 1, 'is_seed': 1, 'is_admin': 1, 'total_earned': 1}
    ).to_list(20)
    print('LB_SEED users:', lb_seed_users)
    
    # Check all users with is_seed flag
    all_seed = await db.users.find(
        {'is_seed': True},
        {'_id': 0, 'id': 1, 'name': 1, 'is_seed': 1}
    ).to_list(20)
    print('All is_seed users:', all_seed)

asyncio.run(check())
