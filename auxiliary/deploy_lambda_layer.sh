pip install --target ./python -r shared/requirements.txt
cp -r shared/ python/shared/
cp -r dynamodb/ python/dynamodb/
zip -r lambda_layer.zip python/

aws lambda publish-layer-version --layer-name ExtremeStatupLayer \
    --zip-file fileb://lambda_layer.zip \
    --compatible-runtimes python3.9 \
    --compatible-architectures "x86_64"

rm -r python/
rm lambda_layer.zip