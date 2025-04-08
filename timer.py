
import asyncio
import time

class GameTimer:
    def __init__(self, initial_time=60):
        self.time_left = initial_time
        self.start_time = time.time()
        self.is_running = False
        self.callbacks = []

    def add_callback(self, callback):
        self.callbacks.append(callback)

    def extend(self, seconds):
        self.time_left += seconds
        return self.time_left

    async def start(self):
        self.is_running = True
        self.start_time = time.time()

        while self.is_running and self.time_left > 0:
            current_time = time.time()
            elapsed = current_time - self.start_time
            self.time_left = max(0, self.initial_time - elapsed)
            
            # Auto-start check
            if self.room and len(self.room.players) >= 4 and self.time_left <= 0:
                from game_logic import start_game
                await start_game(self.room, self.context)
                break
            
            for callback in self.callbacks:
                await callback(self.time_left)
                
            if self.time_left <= 0:
                self.is_running = False
                break
                
            await asyncio.sleep(1)  # Update every second

    def stop(self):
        self.is_running = False
