"""
Migration script to add missing fields to the User table
"""
from tortoise import Tortoise, run_async
from app.config import get_database_url

async def run():
    # Connect to the database
    await Tortoise.init(
        db_url=get_database_url(),
        modules={"models": ["app.models.user"]}
    )
    
    # Get connection
    connection = Tortoise.get_connection("default")
    
    # Add missing columns to the User table
    # These columns are defined in the model but missing in the database
    await connection.execute_script("""
    ALTER TABLE "user" 
    ADD COLUMN IF NOT EXISTS position VARCHAR(255),
    ADD COLUMN IF NOT EXISTS department VARCHAR(255),
    ADD COLUMN IF NOT EXISTS phone VARCHAR(50),
    ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(500),
    ADD COLUMN IF NOT EXISTS last_login TIMESTAMP;
    """)
    
    print("Migration completed successfully!")
    
    # Close connections
    await Tortoise.close_connections()

if __name__ == "__main__":
    run_async(run())
