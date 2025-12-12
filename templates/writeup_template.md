# {{CTF_NAME}} — Writeup

## Challenge Information

**Category:** Pwn
**Difficulty:**
**Points:**
**Solves:**
**Author:**

## Challenge Description

> (Paste challenge description here)

## Files Provided

- Binary:
- libc:
- Other:

## Initial Analysis

### Security Mitigations

(See analysis.md for full checksec output)

- **PIE:**
- **NX:**
- **Canary:**
- **RELRO:**
- **ASLR:**

### Key Observations

-
-
-

## Vulnerability

### Type

(Buffer overflow, UAF, format string, integer overflow, etc.)

### Location

(Function name and line/offset if source is available)

### Description

(Explain how the vulnerability works)

## Exploitation Strategy

### Approach

1.
2.
3.

### Challenges

(Any protections or difficulties to overcome)

-
-

### Bypasses/Techniques

(How you bypassed mitigations)

-
-

## Solution

### Step-by-Step

#### 1. Information Leak

(If applicable - e.g., leaking libc address, stack address, etc.)

```python
# Code snippet
```

#### 2. Building the Payload

```python
# Code snippet
```

#### 3. Exploitation

```python
# Final exploit code
```

### Local Testing

```bash
# Commands used for local testing
./exploit.py LOCAL
```

### Remote Exploitation

```bash
# Commands for remote
./exploit.py HOST=ctf.example.com PORT=1337
```

## Flag

```
flag{...}
```

## Alternative Solutions

(If you discovered other ways to solve it)

## Lessons Learned

-
-

## References

-
-

## Tools Used

- pwntools
- GDB/pwndbg
-

## Notes

(Any additional notes, debugging tips, or observations)
