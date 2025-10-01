# ArionKoder Python Challenges

## Setup

Create and activate a virtual environment:
```bash
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

Install all dependencies:
```bash
pip install -r requirements.txt
```

## How to Run

### Challenge 1: Memory-Efficient Data Pipeline
```bash
cd challenge_1_pipeline
python pipeline.py
```

### Challenge 2: Custom Context Manager
```bash
cd challenge_2_context
python context_manager.py
```

### Challenge 3: Advanced Meta-Programming
```bash
cd challenge_3_meta
python metaclass_system.py
```

### Challenge 4: Custom Iterator with Lazy Evaluation
```bash
cd challenge_4_iterator
python lazy_collection.py
```

### Challenge 5: Distributed Task Scheduler
```bash
cd challenge_5_scheduler
python scheduler.py
```

## Running Tests

Each challenge includes tests that can be run with pytest:
```bash
cd challenge_X_name
pytest test_*.py
```
