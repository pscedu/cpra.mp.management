import uvicorn
from cpra.mp.management.database import create_all
from cpra.mp.management import app

create_all()

uvicorn.run(app, host="0.0.0.0", port=5000)
