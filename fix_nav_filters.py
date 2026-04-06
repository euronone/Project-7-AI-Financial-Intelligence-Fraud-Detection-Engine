#!/usr/bin/env python3
"""
Fix all dashboard pages to hide Test Me from analysts
Add: isAdmin import and .filter() to nav rendering
"""

import os
import re

frontend_path = r"c:\Users\gsuni\OneDrive\Desktop\AI_Project\AI-Financial-Intelligence-Fraud\frontend\app\dashboard"

pages = [
    "transactions/page.tsx",
    "alerts/page.tsx",
    "customers/page.tsx",
    "data-sources/page.tsx",
    "settings/page.tsx",
    "test-me/page.tsx",
    "ml-details/page.tsx",
]

for page in pages:
    filepath = os.path.join(frontend_path, page)
    if not os.path.exists(filepath):
        print(f"[SKIP] {page} - not found")
        continue

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if already fixed
    if ".filter(({ adminOnly })" in content:
        print(f"[OK] {page} - already has filter")
        continue

    # 1. Add isAdmin import if not present
    if "import { useAuthStore, isAdmin }" not in content:
        content = content.replace(
            "import { useAuthStore } from \"@/store/auth-store\";",
            "import { useAuthStore, isAdmin } from \"@/store/auth-store\";"
        )

    # 2. Add adminOnly field to Test Me nav item
    content = re.sub(
        r'(\{[^}]*icon:\s*FlaskConical[^}]*label:\s*"Test Me"[^}]*href:\s*"/dashboard/test-me"[^}]*)(\s*\})',
        r'\1, adminOnly: true\2',
        content,
        flags=re.DOTALL
    )

    # 3. Add adminOnly: false to other items if missing
    content = re.sub(
        r'(\{[^}]*icon:\s*(?!FlaskConical)[^}]*label:\s*"(?!Test Me)"[^}]*href:[^}]*)(\s*\})',
        r'\1, adminOnly: false\2',
        content,
        count=20,
        flags=re.DOTALL
    )

    # 4. Add filter before .map()
    # Find pattern: [ {...}, {...} ].map(
    content = re.sub(
        r'(\]\s*)\.map\(\(\{\s*icon:\s*Icon,\s*label,\s*href,\s*active\s*\}\s*\)',
        r'\1.filter(({ adminOnly }) => !adminOnly || isAdmin(user))\n            .map(({ icon: Icon, label, href, active }) =>',
        content
    )

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"[FIXED] {page}")

print("\n[SUCCESS] All pages updated!")
