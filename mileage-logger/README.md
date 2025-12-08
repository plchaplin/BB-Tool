# Mileage Logger

This is a simple command-line tool for logging mileage.

## How to Use

**Note:** All commands should be run from the root of the project directory.

### Compile the code
```bash
javac mileage-logger/MileageLogger.java
```

### Add a new mileage entry
```bash
java -cp mileage-logger MileageLogger add <date> <miles>
```
**Example:**
```bash
java -cp mileage-logger MileageLogger add 2025-12-08 100
```

### List all mileage entries
```bash
java -cp mileage-logger MileageLogger list
```

All mileage data is stored in `mileage.csv` in the project root.
