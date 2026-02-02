# BRAND BOOK: Antigravity Design System

> **Vision**: High-End, Premium, Tech-Forward. Merging "Clean Design" with "Glassmorphism" to create an immersive, authority-building aesthetic.

## 1. Core Philosophy
- **White Space is Luxury**: We do not clutter. We let the content breathe.
- **Glassmorphism**: Depth through translucency. Layers imply complexity managed with elegance.
- **Neuro-Design**:
    - **F-Pattern**: Key information (Impact/ROI) placed where the eye naturally lands.
    - **Cognitive Ease**: High contrast for readability, low friction for scanning.
    - **Authority**: Use of distinct, strong typography to command respect.

## 2. Typography
We use a **Modern Geometric Sans-Serif** pairing for maximum screen legibility and premium feel.

- **Primary Headings (Display)**: `Outfit`
    - Weights: Bold (700), SemiBold (600)
    - Usage: Names, Job Titles, Section Headers.
    - Tracking: Tight (-0.02em) for a compact, modern look.

- **Body Text**: `Inter`
    - Weights: Regular (400), Medium (500)
    - Usage: Descriptions, Bullets, detailed text.
    - Line-Height: 1.6 (Premium readability / White spacing).

- **Code / Technical**: `JetBrains Mono`
    - Usage: Tech Stack lists, Metadata.

## 3. Color Palette (Dark Mode First)

### Backgrounds
- **Void Black**: `#09090b` (Rich black, not flat #000)
- **Deep Layer**: `#18181b` (Zinc 900)

### Glassmorphism (Surfaces)
- **Glass Panel**: `rgba(255, 255, 255, 0.03)` + Blur 20px
- **Glass Border**: `rgba(255, 255, 255, 0.08)` (1px solid)
- **Glass Highlight**: `rgba(255, 255, 255, 0.15)` (Top border only to catch "light")

### Text & Accents
- **Text Primary**: `#fafafa` (Zinc 50)
- **Text Secondary**: `#a1a1aa` (Zinc 400)
- **Text Tertiary**: `#52525b` (Zinc 600 - subtle details)
- **Accent (The "Glow")**: `linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)` (Blue to Violet)
- **ROI Highlight**: `#10b981` (Emerald 500 - used sparingly for metrics/results)

## 4. UI Library (Components)

### The "Card"
- Rounded corners: `rounded-2xl`
- Backdrop blur: `backdrop-blur-xl`
- Border: 1px solid `white/10`
- Shadow: `shadow-2xl` black/50

### Interactive Elements
- **Hover**: Scale 1.02 + Brightness 1.1 + Border turns to Accent.
- **Active**: Scale 0.98.

## 5. ATS & Scannability (The Architecture)
While the Web CV uses Glassmorphism, the **Resume Document (PDF/LaTeX)** must remain **ATS Friendly**.
- **Rule**: No floating layers or complex gradients in the text layer of the ATS version.
- **Strategy**: Use the *structure* and *typography* to convey the brand, but strictly adhere to linear parsing.

## 6. Tone of Voice
- **Direct & Senior**: "Led migration", not "Helped with migration".
- **Metric-First**: "Reduced latency by 40%", not "Improved performance".
- **Polished**: Zero fluff. Every word must earn its pixel.
