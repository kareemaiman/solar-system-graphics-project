import sys
from gameplay.engine import Engine
from core.logger import logger

def main():
    engine = Engine()
    return engine.run()

if __name__ == '__main__':
    while True:
        try:
            should_restart = main()
            if not should_restart:
                break
            logger.info("Main loop re-initializing...")
        except Exception as e:
            logger.error(f"Fatal error in main loop: {e}", exc_info=True)
            break
