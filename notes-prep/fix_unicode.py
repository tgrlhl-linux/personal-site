#!/usr/bin/env python3
"""Fix HTML entities in generated markdown files to actual Unicode characters."""

import os
import re
import html

NOTES_DIR = r'E:\Claudecode\personal-site\notes-prep'

# Manually curated mapping of HTML entities to Unicode for math symbols
ENTITY_MAP = {
    # Greek letters
    '&#x03A3;': 'Σ',  # Σ
    '&#x03C3;': 'σ',  # σ
    '&#x03BC;': 'μ',  # μ
    '&#x03B1;': 'α',  # α
    '&#x03B2;': 'β',  # β
    '&#x03C0;': 'π',  # π
    '&#x03BB;': 'λ',  # λ
    '&#x03B5;': 'ε',  # ε
    '&#x03B8;': 'θ',  # θ
    '&alpha;': 'α',
    '&beta;': 'β',
    '&pi;': 'π',
    '&lambda;': 'λ',
    '&mu;': 'μ',
    '&sigma;': 'σ',
    '&theta;': 'θ',
    '&epsilon;': 'ε',

    # Math operators
    '&#x2264;': '≤',  # ≤
    '&#x2265;': '≥',  # ≥
    '&#x2211;': '∑',  # ∑
    '&#x222B;': '∫',  # ∫
    '&#x00D7;': '×',  # ×
    '&#x00B2;': '²',  # ²
    '&#x2212;': '−',  # −
    '&#x2248;': '≈',  # ≈

    # Subscripts
    '&#x2080;': '₀',  # ₀
    '&#x2081;': '₁',  # ₁
    '&#x2082;': '₂',  # ₂
    '&#x2083;': '₃',  # ₃
    '&#x1D55;': 'ᵕ',  # ᵕ  (small superscript modifier)

    # Set theory / logic
    '&#x2229;': '∩',  # ∩
    '&#x222A;': '∪',  # ∪
    '&#x2286;': '⊆',  # ⊆
    '&#x2288;': '⊈',  # ⊈
    '&#x2203;': '∃',  # ∃
    '&#x2192;': '→',  # →
    '&#x21D2;': '⇒',  # ⇒
    '&#x21D4;': '⇔',  # ⇔
    '&#x2260;': '≠',  # ≠

    # Named entities often used in math
    '&sum;': '∑',
    '&prod;': '∏',
    '&int;': '∫',
    '&radic;': '√',
    '&infin;': '∞',
    '&cup;': '∪',
    '&cap;': '∩',
    '&sube;': '⊆',
    '&supe;': '⊇',
    '&isin;': '∈',
    '&notin;': '∉',
    '&rarr;': '→',
    '&rArr;': '⇒',
    '&hArr;': '⇔',
    '&ne;': '≠',
    '&le;': '≤',
    '&ge;': '≥',
    '&times;': '×',
    '&sup2;': '²',
    '&sup3;': '³',
    '&plusmn;': '±',

    # Remaining decimal entities
    '&#x207B;': '⁻',  # ⁻
    '&#x207F;': 'ⁿ',  # ⁿ
    '&#x00B0;': '°',  # °
    '&#x00B7;': '·',  # ·
    '&#x2122;': '™',  # ™

    # Bare Greek letter names (missing & prefix)
    'mu;': 'μ',
    'Mu;': 'Μ',
    'sigma;': 'σ',
    'Sigma;': 'Σ',
    'alpha;': 'α',
    'beta;': 'β',
    'theta;': 'θ',
    'lambda;': 'λ',
    'pi;': 'π',
    'epsilon;': 'ε',

    # Special
    '&#x25B3;': '△',  # △
    '&#x25CB;': '○',  # ○
    '&#x2713;': '✓',  # ✓
    '&#x2717;': '✗',  # ✗
    '&#x2605;': '★',  # ★
}

def fix_entities(text):
    """Replace known HTML entities with actual Unicode. Falls back to html.unescape."""
    for entity, char in ENTITY_MAP.items():
        text = text.replace(entity, char)
    # Also handle any remaining hex entities like &#xNNNN;
    remaining = re.findall(r'&#x[0-9a-fA-F]+;', text)
    for ent in remaining:
        try:
            num = int(ent[3:-1], 16)
            text = text.replace(ent, chr(num))
        except:
            pass
    # Handle decimal entities like &#NNNN;
    remaining = re.findall(r'&#[0-9]+;', text)
    for ent in remaining:
        try:
            num = int(ent[2:-1])
            text = text.replace(ent, chr(num))
        except:
            pass
    return text

def main():
    count = 0
    total_fixes = 0

    for fn in sorted(os.listdir(NOTES_DIR)):
        if not fn.endswith('.md'):
            continue
        path = os.path.join(NOTES_DIR, fn)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Count original entities
        orig_entities = len(re.findall(r'&[#a-zA-Z0-9]{2,8};', content))

        fixed = fix_entities(content)

        if fixed != content:
            # Count remaining entities
            rem_entities = len(re.findall(r'&[#a-zA-Z0-9]{2,8};', fixed))
            fixes = orig_entities - rem_entities
            with open(path, 'w', encoding='utf-8') as f:
                f.write(fixed)
            print(f'  OK {fn}: {fixes} entities fixed')
            count += 1
            total_fixes += fixes

    print(f'Done. Fixed {total_fixes} entities in {count} files')

if __name__ == '__main__':
    main()
