import aiosqlite


class DataManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.db = None
        

    async def connect(self):
        self.db = await aiosqlite.connect(self.db_path)
        await self.db.execute("PRAGMA foreign_keys = ON;")
        await self.db.commit()

    async def setup(self):
        await self.db.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            guild_id TEXT,
            user_id TEXT,
            score INTEGER DEFAULT 0,
            PRIMARY KEY (guild_id, user_id)
        )
        """)

        await self.db.execute("""
        CREATE TABLE IF NOT EXISTS locations (
            user_id TEXT PRIMARY KEY,
            lat REAL,
            lng REAL
        )
        """)

    async def add_score(self, guild_id, user_id, score):
        await self.db.execute("""
        INSERT INTO scores (guild_id, user_id, score)
        VALUES (?, ?, ?)
        ON CONFLICT(guild_id, user_id)
        DO UPDATE SET score = score + ?
        """, (guild_id, user_id, score, score))

    async def get_leaderboard(self, guild_id, limit=10):
        cursor = await self.db.execute("""
        SELECT user_id, score
        FROM scores
        WHERE guild_id = ?
        ORDER BY score DESC
        LIMIT ?
        """, (guild_id, limit))

        return await cursor.fetchall()
    
    async def set_location(self, user_id, lat, lng):
        await self.db.execute("""
        INSERT INTO locations (user_id, lat, lng)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id)
        DO UPDATE SET lat = ?, lng = ?
        """, (user_id, lat, lng, lat, lng))

        await self.db.commit()

    async def get_location(self, user_id):
        cursor = await self.db.execute("""
        SELECT lat, lng FROM locations WHERE user_id = ?
        """, (user_id,))

        return await cursor.fetchone()