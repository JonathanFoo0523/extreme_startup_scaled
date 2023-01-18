mkdir python
cp -r request_response.py python/request_response.py
zip -r api_layer.zip python/

aws lambda publish-layer-version --layer-name ExtremeStartupAPI \
    --zip-file fileb://api_layer.zip \
    --compatible-runtimes python3.9 \
    --compatible-architectures "x86_64"

rm -r python/
rm api_layer.zip