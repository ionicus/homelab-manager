# Backend Scripts

Utility scripts for managing the Homelab Manager backend.

## Test Data Management

### manage_test_data.py

Manages test data in the database. All test devices should be prefixed with `TEST_`.

**Usage:**

```bash
# From backend directory
source .venv/bin/activate

# Delete all TEST_ prefixed devices
python scripts/manage_test_data.py flush

# Create sample test data
python scripts/manage_test_data.py create

# Delete and recreate test data
python scripts/manage_test_data.py reset
```

**Convention:**
- All test devices must have names starting with `TEST_`
- This allows easy cleanup without affecting production data
- Example: `TEST_server-01`, `TEST_docker-vm`, `TEST_nginx-container`

**Sample Test Devices Created:**
- `TEST_server-01` - Physical server
- `TEST_docker-vm` - Virtual machine
- `TEST_nginx-container` - Container
- `TEST_main-switch` - Network device
