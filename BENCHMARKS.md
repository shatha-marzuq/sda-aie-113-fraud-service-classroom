### Multi-stage build (final, with pandas)
- Image size: 166.7 MB (target: ≤ 450 MB) 
- Warm rebuild: 30.9s (target: < 30s) 
- Runtime user: appuser (non-root) 

### Compose stack
- fraud-api: healthy 
- feature-cache: healthy 

### Smoke test (containerised)
- /v1/ready: 200 
- /v1/predict: 200, matches bare-metal Lab 2 result (0.185852) 