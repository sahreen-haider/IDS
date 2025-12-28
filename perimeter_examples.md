# Perimeter Zone Configuration Guide

## Understanding Normalized Coordinates

Coordinates are normalized from 0.0 to 1.0:
- `x: 0.0` = left edge, `x: 1.0` = right edge
- `y: 0.0` = top edge, `y: 1.0` = bottom edge

```
(0.0, 0.0) ──────────────────── (1.0, 0.0)
     │                              │
     │                              │
     │         CAMERA VIEW          │
     │                              │
     │                              │
(0.0, 1.0) ──────────────────── (1.0, 1.0)
```

## Common Perimeter Patterns

### 1. Full Frame (No Restriction)
Entire camera view is monitored:
```yaml
perimeter_zone:
  - [0.0, 0.0]
  - [1.0, 0.0]
  - [1.0, 1.0]
  - [0.0, 1.0]
```

### 2. Center Zone (50% of frame)
Monitor only the center area:
```yaml
perimeter_zone:
  - [0.25, 0.25]  # 25% from left, 25% from top
  - [0.75, 0.25]  # 75% from left, 25% from top
  - [0.75, 0.75]  # 75% from left, 75% from top
  - [0.25, 0.75]  # 25% from left, 75% from top
```

```
┌───────────────────────┐
│                       │
│   ┌───────────────┐   │
│   │               │   │  ← Only alerts here
│   │   CENTER      │   │
│   │               │   │
│   └───────────────┘   │
│                       │
└───────────────────────┘
```

### 3. Bottom Half (Entrance/Floor)
Monitor floor or entrance area:
```yaml
perimeter_zone:
  - [0.0, 0.5]
  - [1.0, 0.5]
  - [1.0, 1.0]
  - [0.0, 1.0]
```

```
┌───────────────────────┐
│                       │  ← Ignored
│      IGNORED          │
├───────────────────────┤ ← 50% line
│                       │
│   MONITORED ZONE      │  ← Alerts triggered
│                       │
└───────────────────────┘
```

### 4. Doorway/Entrance
Vertical strip for monitoring doorways:
```yaml
perimeter_zone:
  - [0.3, 0.0]
  - [0.7, 0.0]
  - [0.7, 1.0]
  - [0.3, 1.0]
```

```
┌───────────────────────┐
│   │           │       │
│ X │  DOORWAY  │  X    │
│   │           │       │
│ X │ MONITORED │  X    │  ← Only center strip
│   │           │       │
│ X │           │  X    │
└───────────────────────┘
     (X = ignored areas)
```

### 5. Diagonal Zone
Custom angled zone:
```yaml
perimeter_zone:
  - [0.1, 0.2]
  - [0.6, 0.1]
  - [0.9, 0.6]
  - [0.8, 0.9]
  - [0.3, 0.8]
```

```
┌───────────────────────┐
│  ┌────────┐           │
│  │        │\          │
│  │  ZONE   │\         │
│  │         │ \        │
│  │          │ \       │
│   \         │  │      │
│    \─────────┘ │      │
└───────────────────────┘
```

### 6. L-Shaped Zone
Monitor corner area:
```yaml
perimeter_zone:
  - [0.0, 0.5]
  - [0.5, 0.5]
  - [0.5, 0.0]
  - [1.0, 0.0]
  - [1.0, 1.0]
  - [0.0, 1.0]
```

```
┌───────────────────────┐
│           │           │
│  IGNORED  │ MONITORED │
│           │           │
├───────────┤           │
│                       │
│    MONITORED ZONE     │
│                       │
└───────────────────────┘
```

## How to Configure Your Perimeter

1. **Enable perimeter detection** in `config.yaml`:
   ```yaml
   enable_perimeter: true
   ```

2. **Run the system** and observe your camera view

3. **Identify the area** you want to monitor:
   - Entrance/door
   - Specific room area
   - Pathway
   - Restricted zone

4. **Estimate coordinates**:
   - Look at object positions on screen
   - Estimate as fractions (0.25 = 25%, 0.5 = 50%, 0.75 = 75%)

5. **Update `perimeter_zone`** in `config.yaml`

6. **Test**: Objects inside the green zone trigger alerts, outside are ignored

## Tips

- **Start simple**: Use rectangular zones first
- **Green overlay**: The system draws a green semi-transparent overlay showing your zone
- **Status display**: Shows "IN ZONE: X | OUTSIDE: Y" object counts
- **Fine-tune**: Adjust coordinates by 0.05-0.1 increments to refine
- **Polygon support**: You can use any number of points (minimum 3)

## Real-World Examples

### Home Front Door
```yaml
# Monitor the doorway and entrance area
perimeter_zone:
  - [0.2, 0.1]   # Above door
  - [0.8, 0.1]
  - [0.9, 0.9]   # Floor in front of door
  - [0.1, 0.9]
```

### Parking Spot
```yaml
# Monitor specific parking space
perimeter_zone:
  - [0.3, 0.4]
  - [0.7, 0.4]
  - [0.8, 0.8]
  - [0.2, 0.8]
```

### Fence Line
```yaml
# Bottom strip monitoring fence perimeter
perimeter_zone:
  - [0.0, 0.7]
  - [1.0, 0.7]
  - [1.0, 1.0]
  - [0.0, 1.0]
```
