from pathlib import Path
from datetime import datetime

rules_dir = Path(__file__).resolve().parent.parent / 'rules'
if not rules_dir.exists():
    raise SystemExit(f'rules dir missing: {rules_dir}')

for f in sorted(rules_dir.glob('*.md')):
    text = f.read_text(encoding='utf-8')
    if '**Source:** CLAUDE.md' in text:
        print('Already updated:', f.name)
        continue
    header = '# Auto-sync metadata (source: CLAUDE.md, updated %s)\n\n**Source:** CLAUDE.md\n\n' % datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    f.write_text(header + text, encoding='utf-8')
    print('Updated:', f.name)

print('Sync done')