from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
forbidden_names = {'.env'}
forbidden_suffixes = {'.pth', '.pt', '.ckpt', '.onnx', '.mp4', '.avi', '.mov', '.mkv'}
problems = []
for p in root.rglob('*'):
    if '.git' in p.parts or not p.is_file():
        continue
    if p.name in forbidden_names or p.suffix.lower() in forbidden_suffixes:
        problems.append(str(p.relative_to(root)))
    if p.stat().st_size > 50 * 1024 * 1024:
        problems.append(f'{p.relative_to(root)} (>50MB)')
if problems:
    print('Refuse to commit potentially unsafe/large files:')
    for x in problems:
        print(' -', x)
    sys.exit(1)
print('Repository file check passed.')
