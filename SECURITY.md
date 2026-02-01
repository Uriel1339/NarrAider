# Security & Privacy

**Created by Andreas "Uriel1339" Lopez**

## Overview

NarrAider is designed to run entirely on your local machine with no external network access. All AI generation happens locally using your own hardware and models.

## Security Features

### Local-Only Operation

- **No Internet Required**: Once models are downloaded, NarrAider works completely offline
- **No Data Collection**: Nothing you generate is sent anywhere
- **No Telemetry**: No usage statistics or analytics
- **No API Calls**: No cloud services or external APIs

### Network Security

**Port Binding**: The llama.cpp server explicitly binds to `127.0.0.1` (localhost only):
- Port 8081 is bound to localhost only
- Cannot be accessed from other devices on your network
- Cannot be accessed from the internet
- Only your local machine can connect

**Network Verification**:
```bash
# Verify server is localhost-only (when running)
netstat -an | findstr 8081
# Should show: 127.0.0.1:8081 (not 0.0.0.0:8081)
```

### File System Access

**Read Access**:
- Config file: `narraider_config.json`
- Model files: Specified in config
- Output folder: `outputs/` (or custom path)

**Write Access**:
- Output files only: Written to `outputs/` subfolder
- Config file: Only when using Setup Wizard
- No access to system files or other user data

### Model Security

**Model Files**:
- You download models from trusted sources (HuggingFace)
- Models run locally through llama.cpp (audited open-source project)
- No external model loading or runtime downloads

**Recommended Sources**:
- HuggingFace: https://huggingface.co/ (verify publisher reputation)
- TheBloke's quantizations (trusted community member)
- Official model releases from known organizations

## Privacy Guarantees

### What Stays Private

**Everything**:
- Your prompts
- Generated content
- Model choices
- All output files
- Usage patterns

**Nothing leaves your machine** - ever.

### Output Files

Generated files are saved locally to:
```
NarrAider/outputs/
├── characters/
├── magic_systems/
├── scenes/
└── [other content types]/
```

**You control**:
- Where files are saved
- Who has access to them
- Whether to share them
- When to delete them

## Best Practices

### Model Downloads

1. **Only download from trusted sources**:
   - Official HuggingFace repositories
   - Well-known quantizers (TheBloke, bartowski, etc.)
   - Verify model checksums when available

2. **Scan downloaded files** (optional paranoia):
   ```bash
   # Windows Defender
   MpCmdRun.exe -Scan -ScanType 3 -File "path\to\model.gguf"
   ```

### Firewall Configuration

**Windows Defender Firewall**:
- NarrAider doesn't require any firewall rules
- If prompted, you can safely block public/internet access
- Only allow private network access if you want to (not required)

**Recommendation**: No firewall rules needed - everything is localhost.

### Secure Model Storage

Store models outside NarrAider folder:
```
YourProjectFolder/
├── NarrAider/          # Git-tracked code
├── models/             # .gitignore'd, local only
└── llama_server/       # .gitignore'd, local only
```

The `.gitignore` prevents accidentally committing large model files.

## Threat Model

### What NarrAider Protects Against

**Network Attacks**: ✅
- Server only binds to localhost
- No internet exposure possible

**Data Exfiltration**: ✅
- No network communication
- No telemetry or analytics

**Unauthorized Access**: ✅
- Standard file system permissions
- No server authentication needed (localhost only)

### What You Need to Protect

**Physical Access**:
- Secure your computer with password/encryption
- Lock screen when away
- Standard OS security practices

**Model Sources**:
- Download models from trusted sources only
- Verify checksums when available

**Output Files**:
- Don't commit sensitive output to public repos
- Use `.gitignore` for outputs folder

## Security Verification

### Check Server Binding

When NarrAider is running:

**Windows**:
```bash
netstat -an | findstr 8081
```

Should show:
```
TCP    127.0.0.1:8081         0.0.0.0:0              LISTENING
```

NOT:
```
TCP    0.0.0.0:8081           0.0.0.0:0              LISTENING  # ❌ BAD
```

**Linux/Mac**:
```bash
lsof -i :8081
# or
netstat -an | grep 8081
```

### Verify No External Connections

```bash
# Windows
netstat -an | findstr ESTABLISHED | findstr python
# Should show no connections to external IPs when idle

# Linux/Mac
netstat -an | grep ESTABLISHED | grep python
```

## Reporting Security Issues

If you discover a security vulnerability:

1. **Do NOT open a public GitHub issue**
2. Contact: [Your preferred contact method]
3. Include:
   - Description of the issue
   - Steps to reproduce
   - Impact assessment
   - Suggested fix (if you have one)

## License & Disclaimer

NarrAider is provided under the MIT License.

**AS-IS, NO WARRANTY**: This software is provided without warranty. Use at your own risk. The authors are not responsible for:
- Data loss
- Security breaches from misconfiguration
- Malicious models from untrusted sources
- System damage from improper use

See [LICENSE.md](LICENSE.md) for full legal text.

---

**Questions about security?** See [README.md](README.md) for general documentation or open a GitHub discussion.
