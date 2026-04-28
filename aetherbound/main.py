import sys # Standard system library
from gameplay.engine import Engine # Simulation core
from core.logger import logger # Engine logger

def main():
    """The persistent Application Loop.
    Prevents recursion crashes by using an iterative approach to game restarts.

    Args:

    Returns:
      : None

    """
    while True:
        try:
            logger.info("Starting simulation session...")
            engine = Engine()
            should_restart = engine.run()
            
            if not should_restart:
                logger.info("Application shutting down normally.")
                break
                
            logger.info("Restart signal received. Re-initializing engine...")
        except Exception as e:
            logger.error(f"Fatal error in main loop: {e}", exc_info=True)
            break

if __name__ == '__main__':
    main()
