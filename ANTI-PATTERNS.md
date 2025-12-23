# Development Anti-Patterns Identified

This document outlines development anti-patterns found in the GiveawayBot codebase.

---

## 1. **Deprecated `datetime.utcnow()` Usage** 🟡 MEDIUM

**Locations:** Multiple files including:
- `src/models/giveaway.py` (lines 34, 50, 67, 123-125)
- `src/models/guild_config.py` (lines 15, 54)
- `src/services/giveaway_service.py` (lines 49, 51)
- `src/ui/embeds.py` (lines 65, 147, 178)
- `tests/conftest.py` (lines 51, 59, 69)

**Issue:** `datetime.utcnow()` is deprecated in Python 3.12+ and returns a naive datetime object without timezone info.

**Fix:** Use `datetime.now(datetime.timezone.utc)` instead:
```python
from datetime import datetime, timezone
datetime.now(timezone.utc)
```

---

## 2. **Duplicated Code in Cogs**

**Locations:** 
- `src/cogs/admin.py` (lines 422-448, 450-482)
- `src/cogs/tasks.py` (lines 151-174, 176-209)

**Issue:** `_update_giveaway_message` and `_announce_winners` methods are nearly identical in both `AdminCog` and `TasksCog`.

**Fix:** Extract common functionality to a shared utility class or mixin. Consider creating a `GiveawayMessageService` that both cogs can use.

---

## 3. **Missing Error Handling in Database Operations**

**Location:** `src/services/storage_service.py`

**Issue:** Most database operations only check if `_connection` exists but don't handle potential database errors (except for `add_entry` which catches `IntegrityError`). Failed queries could raise unhandled exceptions.

**Example fix:**
```python
async def get_giveaway(self, giveaway_id: int) -> Optional[Giveaway]:
    try:
        # existing code
    except aiosqlite.Error as e:
        logger.error(f"Database error: {e}")
        return None
```

---

## 4. **Test File Contains Method That Doesn't Exist**

**Location:** `tests/integration/test_storage.py` (lines 142-143)

**Issue:** Test calls `storage_service.has_entry()` but the actual method in `StorageService` is named `has_entered()`.

```python
assert await storage_service.has_entry(saved.id, 222222222) is True  # Wrong method name
```

**Fix:** Rename to `has_entered()` to match the actual implementation.

---

## 5. **Broad Exception Catching**

**Location:** `src/cogs/tasks.py` (lines 45-46, 109-110, 149)

**Issue:** Using bare `except Exception as e:` catches all exceptions including system exceptions that should propagate.

```python
except Exception as e:
    logger.error(f"Error in check_giveaways task: {e}")
```

**Fix:** Catch specific exceptions or at minimum re-raise critical ones:
```python
except (discord.DiscordException, aiosqlite.Error) as e:
    logger.error(f"Error: {e}")
```

---

## 6. **Inconsistent Type Annotations**

**Locations:** 
- `src/cogs/admin.py` (lines 422-426, 450-454): Parameters typed as `giveaway` and `winners: list` without specifics
- `src/cogs/tasks.py` (lines 151-156, 176-180): Same issue

**Issue:** Using bare `list` instead of `List[int]` or `list[int]` reduces type safety and IDE support.

**Fix:**
```python
async def _announce_winners(
    self,
    giveaway: Giveaway,
    winners: List[int],
) -> None:
```

---

## 7. **Accessing Internal Storage Directly from Cogs**

**Location:** `src/cogs/tasks.py` line 61

**Issue:** The `TasksCog` accesses `self.giveaway_service.storage.update_giveaway()` directly, bypassing the service layer.

```python
await self.giveaway_service.storage.update_giveaway(giveaway)
```

**Fix:** Add a method to `GiveawayService` to handle this operation, maintaining proper encapsulation.

---

## 8. **No Database Migration Strategy**

**Location:** `src/services/storage_service.py`

**Issue:** Database tables are created with `CREATE TABLE IF NOT EXISTS` but there's no migration strategy for schema changes. Adding or modifying columns will require manual intervention.

**Fix:** Consider using a migration tool like `alembic` or implementing a simple version-based migration system.

---

## 9. **Potential Race Condition in Winner Selection**

**Location:** `src/services/winner_service.py` (lines 21-60)

**Issue:** Between fetching entries and storing winners, the entry list could change. There's no transaction or locking mechanism.

**Fix:** Wrap the winner selection in a database transaction or use `SELECT ... FOR UPDATE` semantics.

---

## 10. **Inconsistent Return Types**

**Locations:**
- `src/services/giveaway_service.py`: Some methods return `Optional[Giveaway]`, others return `Tuple[bool, str]`
- Methods like `end_giveaway` and `cancel_giveaway` have inconsistent patterns

**Issue:** Inconsistent error handling patterns make the API harder to use correctly.

**Fix:** Establish a consistent pattern, such as always returning a result object:
```python
@dataclass
class ServiceResult:
    success: bool
    message: str
    data: Optional[Any] = None
```

---

## Summary

| Severity | Count | Categories |
|----------|-------|------------|
| 🟠 High | 2 | Data integrity, test failures |
| 🟡 Medium | 4 | Code quality, maintainability |
| 🟢 Low | 4 | Style, consistency, architectural |

### Priority Actions:
1. Fix the broken test (`has_entry` → `has_entered`)
2. Address deprecated `datetime.utcnow()` usage
3. Refactor duplicated code in cogs
