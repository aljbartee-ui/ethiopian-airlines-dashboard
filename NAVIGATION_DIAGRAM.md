# Navigation Structure Diagram

## Before (Old Structure)

```
┌─────────────────────────────────────────────────────────┐
│                      HOME PAGE                          │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │    Sales     │  │   Flight     │  │    Route     │ │
│  │   Report     │  │    Load      │  │  Analysis    │ │
│  │              │  │              │  │              │ │
│  │      📊      │  │      ✈️      │  │      🌍      │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│        │                  │                  │         │
└────────┼──────────────────┼──────────────────┼─────────┘
         │                  │                  │
         ▼                  ▼                  ▼
  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
  │    Sales     │  │ Load Factor  │  │    Route     │
  │  Dashboard   │  │  Dashboard   │  │  Analysis    │
  │              │  │              │  │  Dashboard   │
  │  • Charts    │  │  • Charts    │  │  • Charts    │
  │  • Metrics   │  │  • Filters   │  │  • Metrics   │
  │  • Upload    │  │  • Upload    │  │  • Upload    │
  └──────────────┘  └──────────────┘  └──────────────┘
```

**Issues:**
- ❌ Route Analysis at same level as Flight Load
- ❌ Confusing - both are flight-related
- ❌ No clear hierarchy

---

## After (New Structure)

```
┌─────────────────────────────────────────────────────────┐
│                      HOME PAGE                          │
│                                                         │
│         ┌──────────────┐       ┌──────────────┐        │
│         │    Sales     │       │   Flight     │        │
│         │   Report     │       │    Load      │        │
│         │              │       │              │        │
│         │      📊      │       │      ✈️      │        │
│         └──────────────┘       └──────────────┘        │
│               │                       │                │
└───────────────┼───────────────────────┼────────────────┘
                │                       │
                ▼                       ▼
         ┌──────────────┐       ┌──────────────────────┐
         │    Sales     │       │   FLIGHT LOAD MENU   │
         │  Dashboard   │       │                      │
         │              │       │  ┌────────────────┐  │
         │  • Charts    │       │  │ Load Factor 📈 │  │
         │  • Metrics   │       │  └────────────────┘  │
         │  • Upload    │       │          │           │
         └──────────────┘       │  ┌────────────────┐  │
                                │  │Route Analysis🌍│  │
                                │  └────────────────┘  │
                                └──────────┬───────────┘
                                           │
                        ┌──────────────────┴──────────────────┐
                        │                                     │
                        ▼                                     ▼
                ┌──────────────┐                    ┌──────────────┐
                │ Load Factor  │                    │    Route     │
                │  Dashboard   │                    │  Analysis    │
                │              │                    │  Dashboard   │
                │  • Charts    │                    │  • Charts    │
                │  • Filters   │                    │  • Metrics   │
                │  • Upload    │                    │  • Upload    │
                └──────────────┘                    └──────────────┘
```

**Benefits:**
- ✅ Clear hierarchy: Flight Load → Sub-options
- ✅ Related features grouped together
- ✅ Cleaner home page (2 cards vs 3)
- ✅ Better user experience

---

## Navigation Paths

### Path 1: Sales Report
```
Home → Sales Report → Dashboard
```

### Path 2: Load Factor
```
Home → Flight Load → Menu → Load Factor → Dashboard
```

### Path 3: Route Analysis
```
Home → Flight Load → Menu → Route Analysis → Dashboard
```

---

## Back Button Behavior

### Sales Dashboard
```
[← Back to Home]
```

### Flight Load Menu
```
[← Back to Home]
```

### Load Factor Dashboard
```
[← Back to Flight Load]  [🏠 Home]
```

### Route Analysis Dashboard
```
[← Back to Flight Load]  [🏠 Home]
```

---

## URL Structure

```
/                              → Home Page
│
├── /sales-report              → Sales Dashboard
│
└── /flight-load               → Flight Load Menu
    │
    ├── /flight-load/load-factor       → Load Factor Dashboard
    │
    └── /flight-load/route-analysis    → Route Analysis Dashboard
```

---

## User Flow Example

**Scenario**: User wants to check route analysis

**Old Flow** (3 clicks):
1. Click "Route Analysis" on home
2. View dashboard
3. Done

**New Flow** (4 clicks, but more organized):
1. Click "Flight Load" on home
2. See menu with options
3. Click "Route Analysis"
4. View dashboard

**Trade-off**: One extra click, but much clearer organization and context

---

## Mobile View

### Home Page (Mobile)
```
┌─────────────────┐
│  Ethiopian      │
│  Airlines       │
├─────────────────┤
│                 │
│  ┌───────────┐  │
│  │  Sales    │  │
│  │  Report   │  │
│  │    📊     │  │
│  └───────────┘  │
│                 │
│  ┌───────────┐  │
│  │  Flight   │  │
│  │   Load    │  │
│  │    ✈️     │  │
│  └───────────┘  │
│                 │
└─────────────────┘
```

### Flight Load Menu (Mobile)
```
┌─────────────────┐
│ ← Back to Home  │
├─────────────────┤
│  Flight Load    │
│  Analytics      │
├─────────────────┤
│                 │
│  ┌───────────┐  │
│  │   Load    │  │
│  │  Factor   │  │
│  │    📈     │  │
│  └───────────┘  │
│                 │
│  ┌───────────┐  │
│  │   Route   │  │
│  │ Analysis  │  │
│  │    🌍     │  │
│  └───────────┘  │
│                 │
└─────────────────┘
```

**Responsive**: Stacks vertically on mobile, side-by-side on desktop

---

## Summary

**Old**: Flat structure, 3 top-level options
**New**: Hierarchical structure, 2 top-level options with sub-menus

**Result**: Better organization, clearer purpose, improved UX! 🎉

