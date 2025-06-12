#!/bin/bash
mkdir -p .vercel/output/functions
mkdir -p .vercel/output/static

cp -r src/api/*.py .vercel/output/functions/

cp -r src/models/*.joblib .vercel/output/functions/

pip install joblib==1.3.2 numpy==1.26.0 --target .vercel/output/functions --no-deps

chmod -R 755 .vercel/output/functions