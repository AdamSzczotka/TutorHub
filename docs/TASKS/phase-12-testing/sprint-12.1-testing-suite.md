# Phase 12 - Sprint 12.1: Testing Suite

## Tasks 143-147: Comprehensive Testing Implementation

> **Duration**: Week 16 (First half of Phase 12)
> **Goal**: Complete testing infrastructure with unit, integration, E2E, and load testing
> **Dependencies**: Phases 0-11 completed (All features implemented)

---

## 📋 SPRINT OVERVIEW

| Task ID | Description                          | Priority | Estimated Time | Dependencies        |
| ------- | ------------------------------------ | -------- | -------------- | ------------------- |
| 143     | Unit tests setup with Vitest 2.2.1   | Critical | 6h             | All phases complete |
| 144     | Integration tests (tRPC routers)     | Critical | 8h             | Task 143            |
| 145     | E2E tests with Playwright 1.50.0     | Critical | 10h            | Task 144            |
| 146     | Load & performance testing           | High     | 6h             | Task 145            |
| 147     | Coverage reports & CI/CD integration | High     | 4h             | Tasks 143-146       |

**Total Estimated Time**: 34 hours

---

## 🎯 DETAILED TASK BREAKDOWN

### Task 143: Unit Tests Setup with Vitest 2.2.1

**Files**: `vitest.config.ts`, `__tests__/services/`, `__tests__/utils/`, `__tests__/hooks/`
**Reference**: TechnologyStack.md section 10, DevelopmentRoadmap.md task 143

#### Package Installation:

```bash
pnpm add -D vitest@2.2.1 @vitest/ui@2.2.1
pnpm add -D @testing-library/react@16.1.0 @testing-library/jest-dom@6.6.3
pnpm add -D @testing-library/user-event@14.5.2 jsdom@25.0.1
pnpm add -D @vitejs/plugin-react@4.3.4
```

#### Vitest Configuration:

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./vitest.setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      exclude: [
        'node_modules/',
        '.next/',
        'coverage/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/mockData/**',
        '**/__tests__/**',
      ],
      lines: 80,
      functions: 80,
      branches: 75,
      statements: 80,
    },
    include: ['**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'],
    exclude: ['node_modules', '.next', 'coverage', 'dist'],
  },
  resolve: {
    alias: {
      '~': path.resolve(__dirname, './'),
    },
  },
});
```

#### Vitest Setup:

```typescript
// vitest.setup.ts
import '@testing-library/jest-dom';
import { expect, afterEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';

// Clean up after each test
afterEach(() => {
  cleanup();
});

// Mock Next.js router
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
    back: vi.fn(),
    pathname: '/',
    query: {},
    asPath: '/',
  }),
  usePathname: () => '/',
  useSearchParams: () => new URLSearchParams(),
}));

// Mock next-auth
vi.mock('next-auth/react', () => ({
  useSession: () => ({
    data: {
      user: {
        id: 'test-user-id',
        email: 'test@example.com',
        name: 'Test User',
        role: 'ADMIN',
      },
      expires: new Date(Date.now() + 2 * 86400).toISOString(),
    },
    status: 'authenticated',
  }),
  signIn: vi.fn(),
  signOut: vi.fn(),
}));

// Mock environment variables
process.env.DATABASE_URL = 'postgresql://test:test@localhost:5432/test';
process.env.AUTH_SECRET = 'test-secret-for-testing-purposes-only';
process.env.RESEND_API_KEY = 'test-resend-key';
```

#### Service Tests Example:

```typescript
// __tests__/services/auth/userCreationService.test.ts
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { UserCreationService } from '~/server/services/auth/userCreationService';
import { prisma } from '~/server/db/client';
import type { UserRole } from '@prisma/client';

// Mock Prisma
vi.mock('~/server/db/client', () => ({
  prisma: {
    user: {
      create: vi.fn(),
      findUnique: vi.fn(),
      update: vi.fn(),
    },
    student: {
      create: vi.fn(),
    },
    tutor: {
      create: vi.fn(),
    },
    userCreationLog: {
      create: vi.fn(),
    },
  },
}));

describe('UserCreationService', () => {
  let service: UserCreationService;

  beforeEach(() => {
    service = new UserCreationService();
    vi.clearAllMocks();
  });

  describe('generateTempPassword', () => {
    it('should generate a 12-character password', () => {
      const password = service.generateTempPassword();
      expect(password).toHaveLength(12);
    });

    it('should generate unique passwords', () => {
      const password1 = service.generateTempPassword();
      const password2 = service.generateTempPassword();
      expect(password1).not.toBe(password2);
    });

    it('should include uppercase, lowercase, numbers, and symbols', () => {
      const password = service.generateTempPassword();
      expect(password).toMatch(/[A-Z]/);
      expect(password).toMatch(/[a-z]/);
      expect(password).toMatch(/[0-9]/);
      expect(password).toMatch(/[!@#$%^&*]/);
    });
  });

  describe('createUser', () => {
    it('should create a student user successfully', async () => {
      const mockData = {
        email: 'student@example.com',
        name: 'Jan',
        surname: 'Kowalski',
        role: 'STUDENT' as UserRole,
        class: '5',
        parentName: 'Anna Kowalska',
        parentEmail: 'anna@example.com',
        parentPhone: '+48123456789',
      };

      const mockUser = {
        id: 'user-id',
        ...mockData,
        password: 'hashed-password',
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      vi.mocked(prisma.user.create).mockResolvedValue(mockUser as any);

      const result = await service.createUser(mockData, 'admin-id');

      expect(result.success).toBe(true);
      expect(result.user).toBeDefined();
      expect(result.tempPassword).toHaveLength(12);
      expect(prisma.user.create).toHaveBeenCalledOnce();
    });

    it('should create a tutor user successfully', async () => {
      const mockData = {
        email: 'tutor@example.com',
        name: 'Maria',
        surname: 'Nowak',
        role: 'TUTOR' as UserRole,
        bio: 'Experienced math tutor',
        experienceYears: 5,
        hourlyRate: 80,
      };

      const mockUser = {
        id: 'user-id',
        ...mockData,
        password: 'hashed-password',
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      vi.mocked(prisma.user.create).mockResolvedValue(mockUser as any);

      const result = await service.createUser(mockData, 'admin-id');

      expect(result.success).toBe(true);
      expect(result.user).toBeDefined();
      expect(prisma.tutor.create).toHaveBeenCalled();
    });

    it('should throw error if email already exists', async () => {
      vi.mocked(prisma.user.findUnique).mockResolvedValue({
        id: 'existing-user',
        email: 'existing@example.com',
      } as any);

      await expect(
        service.createUser(
          {
            email: 'existing@example.com',
            name: 'Test',
            surname: 'User',
            role: 'STUDENT' as UserRole,
          },
          'admin-id'
        )
      ).rejects.toThrow('Email już istnieje w systemie');
    });

    it('should log user creation in audit trail', async () => {
      const mockData = {
        email: 'test@example.com',
        name: 'Test',
        surname: 'User',
        role: 'STUDENT' as UserRole,
      };

      vi.mocked(prisma.user.create).mockResolvedValue({
        id: 'user-id',
        ...mockData,
      } as any);

      await service.createUser(mockData, 'admin-id');

      expect(prisma.userCreationLog.create).toHaveBeenCalledWith({
        data: expect.objectContaining({
          userId: 'user-id',
          createdByAdminId: 'admin-id',
          action: 'USER_CREATED',
        }),
      });
    });
  });
});
```

#### Utility Tests Example:

```typescript
// __tests__/lib/utils.test.ts
import { describe, it, expect } from 'vitest';
import { cn, formatCurrency, formatDate, getInitials } from '~/lib/utils';

describe('Utils', () => {
  describe('cn - className utility', () => {
    it('should merge class names correctly', () => {
      expect(cn('bg-red-500', 'text-white')).toBe('bg-red-500 text-white');
    });

    it('should handle conditional classes', () => {
      expect(cn('base', true && 'active', false && 'disabled')).toBe(
        'base active'
      );
    });

    it('should override conflicting Tailwind classes', () => {
      const result = cn('bg-red-500', 'bg-blue-500');
      expect(result).toBe('bg-blue-500');
    });
  });

  describe('formatCurrency', () => {
    it('should format PLN currency correctly', () => {
      expect(formatCurrency(100)).toBe('100,00 zł');
    });

    it('should handle decimal values', () => {
      expect(formatCurrency(123.45)).toBe('123,45 zł');
    });

    it('should handle large numbers', () => {
      expect(formatCurrency(1234567.89)).toBe('1 234 567,89 zł');
    });
  });

  describe('formatDate', () => {
    it('should format date in Polish locale', () => {
      const date = new Date('2025-09-15T14:30:00');
      expect(formatDate(date)).toMatch(/15 września 2025/);
    });

    it('should handle custom format', () => {
      const date = new Date('2025-09-15');
      expect(formatDate(date, 'yyyy-MM-dd')).toBe('2025-09-15');
    });
  });

  describe('getInitials', () => {
    it('should extract initials from full name', () => {
      expect(getInitials('Jan Kowalski')).toBe('JK');
    });

    it('should handle single name', () => {
      expect(getInitials('Jan')).toBe('J');
    });

    it('should handle three-part names', () => {
      expect(getInitials('Jan Maria Kowalski')).toBe('JK');
    });

    it('should return empty string for empty input', () => {
      expect(getInitials('')).toBe('');
    });
  });
});
```

#### Hook Tests Example:

```typescript
// __tests__/hooks/useDebounce.test.ts
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useDebounce } from '~/hooks/useDebounce';

describe('useDebounce', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should debounce value changes', async () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      {
        initialProps: { value: 'initial', delay: 300 },
      }
    );

    expect(result.current).toBe('initial');

    // Change value
    rerender({ value: 'updated', delay: 300 });

    // Value should not change immediately
    expect(result.current).toBe('initial');

    // Fast-forward time
    vi.advanceTimersByTime(300);

    await waitFor(() => {
      expect(result.current).toBe('updated');
    });
  });

  it('should cancel previous timeout on rapid changes', async () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 300),
      {
        initialProps: { value: 'first' },
      }
    );

    rerender({ value: 'second' });
    vi.advanceTimersByTime(150);

    rerender({ value: 'third' });
    vi.advanceTimersByTime(150);

    // Should still be initial value
    expect(result.current).toBe('first');

    vi.advanceTimersByTime(150);

    await waitFor(() => {
      expect(result.current).toBe('third');
    });
  });
});
```

#### Package.json Scripts:

```json
{
  "scripts": {
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest run --coverage",
    "test:watch": "vitest --watch"
  }
}
```

**Validation**:

- Vitest configured and running
- All service tests passing
- Utility tests passing
- Hook tests passing
- Test coverage >80%

---

### Task 144: Integration Tests (tRPC Routers)

**Files**: `__tests__/api/routers/`, `__tests__/integration/`
**Reference**: DevelopmentRoadmap.md task 144

#### tRPC Test Helpers:

```typescript
// __tests__/helpers/trpc.ts
import { createInnerTRPCContext } from '~/server/api/trpc';
import { appRouter } from '~/server/api/root';
import type { Session } from 'next-auth';

export function createTestContext(session?: Session) {
  return createInnerTRPCContext({
    session:
      session ||
      ({
        user: {
          id: 'test-user-id',
          email: 'test@example.com',
          name: 'Test User',
          role: 'ADMIN',
        },
        expires: new Date(Date.now() + 2 * 86400).toISOString(),
      } as Session),
  });
}

export function createCaller(session?: Session) {
  const ctx = createTestContext(session);
  return appRouter.createCaller(ctx);
}
```

#### Event Router Tests:

```typescript
// __tests__/api/routers/event.test.ts
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { createCaller } from '../../helpers/trpc';
import { prisma } from '~/server/db/client';
import { TRPCError } from '@trpc/server';

vi.mock('~/server/db/client');

describe('Event Router', () => {
  let caller: ReturnType<typeof createCaller>;

  beforeEach(() => {
    caller = createCaller();
    vi.clearAllMocks();
  });

  describe('create', () => {
    it('should create event successfully', async () => {
      const eventData = {
        title: 'Matematyka - funkcje',
        description: 'Lekcja o funkcjach liniowych',
        subjectId: 'subject-id',
        levelId: 'level-id',
        tutorId: 'tutor-id',
        roomId: 'room-id',
        startTime: new Date('2025-09-15T14:00:00'),
        endTime: new Date('2025-09-15T15:00:00'),
        isGroupLesson: false,
        studentIds: ['student-id-1'],
      };

      const mockEvent = {
        id: 'event-id',
        ...eventData,
        status: 'SCHEDULED',
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      vi.mocked(prisma.event.create).mockResolvedValue(mockEvent as any);

      const result = await caller.event.create(eventData);

      expect(result).toEqual(mockEvent);
      expect(prisma.event.create).toHaveBeenCalledOnce();
    });

    it('should throw error if end time before start time', async () => {
      const invalidData = {
        title: 'Test Event',
        subjectId: 'subject-id',
        levelId: 'level-id',
        tutorId: 'tutor-id',
        startTime: new Date('2025-09-15T15:00:00'),
        endTime: new Date('2025-09-15T14:00:00'),
        studentIds: ['student-id-1'],
      };

      await expect(caller.event.create(invalidData)).rejects.toThrow();
    });

    it('should detect scheduling conflicts', async () => {
      vi.mocked(prisma.event.findMany).mockResolvedValue([
        {
          id: 'existing-event',
          title: 'Existing Event',
          tutorId: 'same-tutor-id',
          startTime: new Date('2025-09-15T14:00:00'),
          endTime: new Date('2025-09-15T15:00:00'),
        } as any,
      ]);

      const conflictingData = {
        title: 'New Event',
        subjectId: 'subject-id',
        levelId: 'level-id',
        tutorId: 'same-tutor-id',
        roomId: 'room-id',
        startTime: new Date('2025-09-15T14:30:00'),
        endTime: new Date('2025-09-15T15:30:00'),
        studentIds: ['student-id-1'],
      };

      await expect(caller.event.create(conflictingData)).rejects.toThrow(
        TRPCError
      );
    });

    it('should enforce room capacity for group lessons', async () => {
      vi.mocked(prisma.room.findUnique).mockResolvedValue({
        id: 'room-id',
        name: 'Sala A',
        capacity: 5,
      } as any);

      const groupLessonData = {
        title: 'Group Lesson',
        subjectId: 'subject-id',
        levelId: 'level-id',
        tutorId: 'tutor-id',
        roomId: 'room-id',
        startTime: new Date('2025-09-15T14:00:00'),
        endTime: new Date('2025-09-15T15:00:00'),
        isGroupLesson: true,
        maxParticipants: 10, // Exceeds room capacity
        studentIds: ['student-1', 'student-2'],
      };

      await expect(caller.event.create(groupLessonData)).rejects.toThrow(
        'Przekroczona pojemność sali'
      );
    });
  });

  describe('update', () => {
    it('should update event successfully', async () => {
      const updateData = {
        id: 'event-id',
        title: 'Updated Title',
        startTime: new Date('2025-09-15T15:00:00'),
      };

      vi.mocked(prisma.event.update).mockResolvedValue({
        id: 'event-id',
        ...updateData,
      } as any);

      const result = await caller.event.update(updateData);

      expect(result.title).toBe('Updated Title');
      expect(prisma.event.update).toHaveBeenCalledOnce();
    });

    it('should throw error if event not found', async () => {
      vi.mocked(prisma.event.update).mockRejectedValue(
        new Error('Record not found')
      );

      await expect(
        caller.event.update({
          id: 'non-existent-id',
          title: 'Test',
        })
      ).rejects.toThrow();
    });
  });

  describe('getAll', () => {
    it('should return all events with filters', async () => {
      const mockEvents = [
        {
          id: 'event-1',
          title: 'Event 1',
          startTime: new Date('2025-09-15T14:00:00'),
        },
        {
          id: 'event-2',
          title: 'Event 2',
          startTime: new Date('2025-09-15T15:00:00'),
        },
      ];

      vi.mocked(prisma.event.findMany).mockResolvedValue(mockEvents as any);

      const result = await caller.event.getAll({
        startDate: new Date('2025-09-15'),
        endDate: new Date('2025-09-16'),
      });

      expect(result).toHaveLength(2);
      expect(prisma.event.findMany).toHaveBeenCalledWith(
        expect.objectContaining({
          where: expect.objectContaining({
            startTime: expect.any(Object),
          }),
        })
      );
    });
  });

  describe('checkConflicts', () => {
    it('should detect tutor conflicts', async () => {
      vi.mocked(prisma.event.findMany).mockResolvedValue([
        {
          id: 'conflict-event',
          title: 'Conflicting Event',
          tutorId: 'tutor-id',
          startTime: new Date('2025-09-15T14:00:00'),
          endTime: new Date('2025-09-15T15:00:00'),
        } as any,
      ]);

      const result = await caller.event.checkConflicts({
        tutorId: 'tutor-id',
        startTime: new Date('2025-09-15T14:30:00'),
        endTime: new Date('2025-09-15T15:30:00'),
      });

      expect(result).toHaveLength(1);
      expect(result[0].id).toBe('conflict-event');
    });

    it('should detect room conflicts', async () => {
      vi.mocked(prisma.event.findMany).mockResolvedValue([
        {
          id: 'room-conflict',
          title: 'Room Conflict',
          roomId: 'room-id',
          startTime: new Date('2025-09-15T14:00:00'),
          endTime: new Date('2025-09-15T15:00:00'),
        } as any,
      ]);

      const result = await caller.event.checkConflicts({
        tutorId: 'different-tutor',
        roomId: 'room-id',
        startTime: new Date('2025-09-15T14:30:00'),
        endTime: new Date('2025-09-15T15:30:00'),
      });

      expect(result).toHaveLength(1);
    });

    it('should return empty array if no conflicts', async () => {
      vi.mocked(prisma.event.findMany).mockResolvedValue([]);

      const result = await caller.event.checkConflicts({
        tutorId: 'tutor-id',
        startTime: new Date('2025-09-15T16:00:00'),
        endTime: new Date('2025-09-15T17:00:00'),
      });

      expect(result).toHaveLength(0);
    });
  });
});
```

#### Authorization Tests:

```typescript
// __tests__/api/routers/auth.test.ts
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { createCaller, createTestContext } from '../../helpers/trpc';
import { TRPCError } from '@trpc/server';
import type { Session } from 'next-auth';

describe('Authorization', () => {
  it('should allow admin to access admin procedures', async () => {
    const adminSession: Session = {
      user: {
        id: 'admin-id',
        email: 'admin@example.com',
        name: 'Admin User',
        role: 'ADMIN',
      },
      expires: new Date(Date.now() + 86400).toISOString(),
    };

    const caller = createCaller(adminSession);

    // Should not throw
    await expect(caller.userManagement.list()).resolves.not.toThrow();
  });

  it('should deny tutor access to admin procedures', async () => {
    const tutorSession: Session = {
      user: {
        id: 'tutor-id',
        email: 'tutor@example.com',
        name: 'Tutor User',
        role: 'TUTOR',
      },
      expires: new Date(Date.now() + 86400).toISOString(),
    };

    const caller = createCaller(tutorSession);

    await expect(caller.userManagement.list()).rejects.toThrow(TRPCError);
  });

  it('should deny student access to tutor procedures', async () => {
    const studentSession: Session = {
      user: {
        id: 'student-id',
        email: 'student@example.com',
        name: 'Student User',
        role: 'STUDENT',
      },
      expires: new Date(Date.now() + 86400).toISOString(),
    };

    const caller = createCaller(studentSession);

    await expect(
      caller.attendance.markAttendance({
        eventId: 'event-id',
        studentId: 'student-id',
        status: 'PRESENT',
      })
    ).rejects.toThrow(TRPCError);
  });
});
```

**Validation**:

- All tRPC routers tested
- Authorization working correctly
- Database operations verified
- Error handling tested

---

### Task 145: E2E Tests with Playwright 1.50.0

**Files**: `e2e/`, `playwright.config.ts`
**Reference**: TechnologyStack.md section 10, DevelopmentRoadmap.md task 145

#### Package Installation:

```bash
pnpm add -D playwright@1.50.0 @playwright/test@1.50.0
npx playwright install
```

#### Playwright Configuration:

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },
  ],

  webServer: {
    command: 'pnpm dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
});
```

#### E2E Test Helpers:

```typescript
// e2e/helpers/auth.ts
import { Page } from '@playwright/test';

export async function loginAsAdmin(page: Page) {
  await page.goto('/auth/login');
  await page.fill('input[name="email"]', 'admin@napiatke.pl');
  await page.fill('input[name="password"]', 'Admin123!@#');
  await page.click('button[type="submit"]');
  await page.waitForURL('/admin/dashboard');
}

export async function loginAsTutor(page: Page) {
  await page.goto('/auth/login');
  await page.fill('input[name="email"]', 'tutor@napiatke.pl');
  await page.fill('input[name="password"]', 'Tutor123!@#');
  await page.click('button[type="submit"]');
  await page.waitForURL('/tutor/dashboard');
}

export async function loginAsStudent(page: Page) {
  await page.goto('/auth/login');
  await page.fill('input[name="email"]', 'student@napiatke.pl');
  await page.fill('input[name="password"]', 'Student123!@#');
  await page.click('button[type="submit"]');
  await page.waitForURL('/student/dashboard');
}
```

#### Critical User Flow Tests:

```typescript
// e2e/flows/user-creation.spec.ts
import { test, expect } from '@playwright/test';
import { loginAsAdmin } from '../helpers/auth';

test.describe('User Creation Flow', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test('should create a new student successfully', async ({ page }) => {
    // Navigate to user management
    await page.goto('/admin/users');
    await page.click('button:has-text("Dodaj użytkownika")');

    // Fill form
    await page.fill('input[name="email"]', 'newstudent@example.com');
    await page.fill('input[name="name"]', 'Jan');
    await page.fill('input[name="surname"]', 'Kowalski');
    await page.selectOption('select[name="role"]', 'STUDENT');
    await page.selectOption('select[name="class"]', '5');

    // Parent info
    await page.fill('input[name="parentName"]', 'Anna Kowalska');
    await page.fill('input[name="parentEmail"]', 'anna@example.com');
    await page.fill('input[name="parentPhone"]', '+48123456789');

    // Submit
    await page.click('button[type="submit"]');

    // Verify success
    await expect(
      page.locator('text=Użytkownik został utworzony')
    ).toBeVisible();
    await expect(page.locator('text=newstudent@example.com')).toBeVisible();

    // Verify temporary password modal
    await expect(page.locator('text=Hasło tymczasowe')).toBeVisible();
  });

  test('should create a new tutor successfully', async ({ page }) => {
    await page.goto('/admin/users');
    await page.click('button:has-text("Dodaj użytkownika")');

    await page.fill('input[name="email"]', 'newtutor@example.com');
    await page.fill('input[name="name"]', 'Maria');
    await page.fill('input[name="surname"]', 'Nowak');
    await page.selectOption('select[name="role"]', 'TUTOR');

    // Tutor-specific fields
    await page.fill('textarea[name="bio"]', 'Experienced math tutor');
    await page.fill('input[name="experienceYears"]', '5');
    await page.fill('input[name="hourlyRate"]', '80');

    await page.click('button[type="submit"]');

    await expect(
      page.locator('text=Użytkownik został utworzony')
    ).toBeVisible();
  });

  test('should validate required fields', async ({ page }) => {
    await page.goto('/admin/users');
    await page.click('button:has-text("Dodaj użytkownika")');

    // Try to submit without filling required fields
    await page.click('button[type="submit"]');

    // Check for validation errors
    await expect(page.locator('text=Email jest wymagany')).toBeVisible();
    await expect(page.locator('text=Imię jest wymagane')).toBeVisible();
    await expect(page.locator('text=Nazwisko jest wymagane')).toBeVisible();
  });

  test('should prevent duplicate email', async ({ page }) => {
    await page.goto('/admin/users');
    await page.click('button:has-text("Dodaj użytkownika")');

    // Try to create user with existing email
    await page.fill('input[name="email"]', 'admin@napiatke.pl');
    await page.fill('input[name="name"]', 'Test');
    await page.fill('input[name="surname"]', 'User');
    await page.selectOption('select[name="role"]', 'STUDENT');

    await page.click('button[type="submit"]');

    await expect(
      page.locator('text=Email już istnieje w systemie')
    ).toBeVisible();
  });
});
```

```typescript
// e2e/flows/lesson-scheduling.spec.ts
import { test, expect } from '@playwright/test';
import { loginAsAdmin } from '../helpers/auth';

test.describe('Lesson Scheduling Flow', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto('/admin/calendar');
  });

  test('should create a new lesson from calendar click', async ({ page }) => {
    // Click on empty slot
    const timeSlot = page.locator('.fc-timegrid-slot[data-time="14:00:00"]');
    await timeSlot.click();

    // Fill event modal
    await page.fill('input[name="title"]', 'Matematyka - funkcje');
    await page.selectOption('select[name="subjectId"]', {
      label: 'Matematyka',
    });
    await page.selectOption('select[name="levelId"]', { label: 'Klasa 5' });
    await page.selectOption('select[name="tutorId"]', { label: 'Maria Nowak' });
    await page.selectOption('select[name="roomId"]', { label: 'Sala A' });

    // Select student
    await page.click('button:has-text("Wybierz uczniów")');
    await page.check('input[value="student-id-1"]');
    await page.click('button:has-text("Potwierdź")');

    await page.click('button[type="submit"]:has-text("Utwórz")');

    // Verify event appears on calendar
    await expect(
      page.locator('.fc-event:has-text("Matematyka - funkcje")')
    ).toBeVisible();
  });

  test('should drag and drop event to new time', async ({ page }) => {
    const event = page.locator('.fc-event').first();
    const newTimeSlot = page.locator('.fc-timegrid-slot[data-time="15:00:00"]');

    // Drag event
    await event.dragTo(newTimeSlot);

    // Verify success notification
    await expect(
      page.locator('text=Zajęcia zostały zaktualizowane')
    ).toBeVisible();
  });

  test('should prevent conflicting events', async ({ page }) => {
    // Create first event
    await page.locator('.fc-timegrid-slot[data-time="14:00:00"]').click();
    await page.fill('input[name="title"]', 'Event 1');
    await page.selectOption('select[name="tutorId"]', { label: 'Maria Nowak' });
    await page.click('button[type="submit"]');

    // Try to create conflicting event
    await page.locator('.fc-timegrid-slot[data-time="14:30:00"]').click();
    await page.fill('input[name="title"]', 'Event 2');
    await page.selectOption('select[name="tutorId"]', { label: 'Maria Nowak' });
    await page.click('button[type="submit"]');

    // Should show conflict error
    await expect(page.locator('text=Konflikt terminów')).toBeVisible();
  });

  test('should switch between calendar views', async ({ page }) => {
    // Switch to day view
    await page.click('button:has-text("Dzień")');
    await expect(page.locator('.fc-timeGridDay-view')).toBeVisible();

    // Switch to week view
    await page.click('button:has-text("Tydzień")');
    await expect(page.locator('.fc-timeGridWeek-view')).toBeVisible();

    // Switch to month view
    await page.click('button:has-text("Miesiąc")');
    await expect(page.locator('.fc-dayGridMonth-view')).toBeVisible();
  });
});
```

```typescript
// e2e/flows/cancellation-makeup.spec.ts
import { test, expect } from '@playwright/test';
import { loginAsStudent, loginAsAdmin } from '../helpers/auth';

test.describe('Cancellation & Makeup Flow', () => {
  test('student requests cancellation', async ({ page }) => {
    await loginAsStudent(page);
    await page.goto('/student/calendar');

    // Click on upcoming lesson
    await page.click('.fc-event').first();

    // Request cancellation
    await page.click('button:has-text("Anuluj zajęcia")');
    await page.fill('textarea[name="reason"]', 'Nieoczekiwana choroba');
    await page.click('button:has-text("Wyślij prośbę")');

    // Verify request submitted
    await expect(
      page.locator('text=Prośba o anulowanie została wysłana')
    ).toBeVisible();
  });

  test('admin approves cancellation', async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto('/admin/cancellations');

    // Find pending request
    const request = page.locator('tr:has-text("Pending")').first();
    await request.click('button:has-text("Zatwierdź")');

    // Add admin comment
    await page.fill(
      'textarea[name="adminComment"]',
      'Zatwierdzam - usprawiedliwiona nieobecność'
    );
    await page.click('button:has-text("Potwierdź zatwierdzenie")');

    // Verify approved
    await expect(page.locator('text=Approved')).toBeVisible();
  });

  test('student reschedules makeup lesson', async ({ page }) => {
    await loginAsStudent(page);
    await page.goto('/student/makeup-lessons');

    // Click on makeup lesson
    const makeupLesson = page.locator('.makeup-lesson-card').first();
    await makeupLesson.click('button:has-text("Przełóż")');

    // Select new date
    await page.click('.fc-timegrid-slot[data-time="16:00:00"]');
    await page.click('button:has-text("Potwierdź")');

    // Verify rescheduled
    await expect(page.locator('text=Zajęcia zostały przełożone')).toBeVisible();
  });
});
```

**Validation**:

- All critical user flows tested
- Cross-browser testing passed
- Mobile responsive tested
- Screenshots on failure captured

---

### Task 146: Load & Performance Testing

**Files**: `load-tests/`, `k6.config.js`
**Reference**: DevelopmentRoadmap.md task 146

#### Package Installation:

```bash
# Install k6 (outside npm)
# https://k6.io/docs/get-started/installation/
```

#### Load Test Scripts:

```javascript
// load-tests/login-flow.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

export const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '30s', target: 10 }, // Ramp up to 10 users
    { duration: '1m', target: 50 }, // Ramp up to 50 users
    { duration: '2m', target: 100 }, // Ramp up to 100 users
    { duration: '1m', target: 100 }, // Stay at 100 users
    { duration: '30s', target: 0 }, // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests under 500ms
    http_req_failed: ['rate<0.01'], // Less than 1% failure rate
    errors: ['rate<0.1'], // Less than 10% error rate
  },
};

const BASE_URL = 'http://localhost:3000';

export default function () {
  // Login
  const loginRes = http.post(`${BASE_URL}/api/auth/login`, {
    email: 'test@example.com',
    password: 'Test123!@#',
  });

  const loginSuccess = check(loginRes, {
    'login status is 200': (r) => r.status === 200,
    'login response time < 500ms': (r) => r.timings.duration < 500,
  });

  errorRate.add(!loginSuccess);

  sleep(1);

  // Fetch dashboard
  const dashboardRes = http.get(`${BASE_URL}/admin/dashboard`);

  const dashboardSuccess = check(dashboardRes, {
    'dashboard status is 200': (r) => r.status === 200,
    'dashboard response time < 1000ms': (r) => r.timings.duration < 1000,
  });

  errorRate.add(!dashboardSuccess);

  sleep(2);
}
```

```javascript
// load-tests/calendar-operations.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 50, // 50 virtual users
  duration: '5m',
  thresholds: {
    http_req_duration: ['p(95)<1000'],
    http_req_failed: ['rate<0.05'],
  },
};

const BASE_URL = 'http://localhost:3000';

export default function () {
  // Fetch events
  const eventsRes = http.get(`${BASE_URL}/api/trpc/event.getAll`);

  check(eventsRes, {
    'events fetched successfully': (r) => r.status === 200,
    'events response time < 500ms': (r) => r.timings.duration < 500,
  });

  sleep(1);

  // Create event
  const createRes = http.post(`${BASE_URL}/api/trpc/event.create`, {
    title: 'Load Test Event',
    subjectId: 'subject-id',
    tutorId: 'tutor-id',
    startTime: new Date().toISOString(),
    endTime: new Date(Date.now() + 3600000).toISOString(),
  });

  check(createRes, {
    'event created': (r) => r.status === 200,
    'create response time < 1000ms': (r) => r.timings.duration < 1000,
  });

  sleep(2);
}
```

#### Performance Monitoring Setup:

```typescript
// lib/performance.ts
export function measurePerformance(name: string, fn: () => Promise<void>) {
  if (typeof window !== 'undefined' && window.performance) {
    const mark = `${name}-start`;
    performance.mark(mark);

    return fn().finally(() => {
      performance.measure(name, mark);
      const measure = performance.getEntriesByName(name)[0];
      console.log(`${name}: ${measure.duration}ms`);
    });
  }

  return fn();
}

export function reportWebVitals(metric: any) {
  console.log(metric);

  // Send to analytics
  if (process.env.NODE_ENV === 'production') {
    // Send to Vercel Analytics or other service
  }
}
```

**Validation**:

- System handles 100+ concurrent users
- 95th percentile response time < 500ms
- Error rate < 1%
- Database queries optimized

---

### Task 147: Coverage Reports & CI/CD Integration

**Files**: `.github/workflows/test.yml`, `vitest.config.ts`
**Reference**: DevelopmentRoadmap.md task 147

#### GitHub Actions Workflow:

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  unit-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Setup pnpm
        uses: pnpm/action-setup@v2
        with:
          version: 8

      - name: Install dependencies
        run: pnpm install

      - name: Run unit tests
        run: pnpm test:coverage

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage/lcov.info
          flags: unittests
          fail_ci_if_error: true

      - name: Check coverage threshold
        run: |
          COVERAGE=$(cat coverage/coverage-summary.json | jq '.total.lines.pct')
          if (( $(echo "$COVERAGE < 80" | bc -l) )); then
            echo "Coverage $COVERAGE% is below 80% threshold"
            exit 1
          fi

  integration-tests:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:17.2
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Setup pnpm
        uses: pnpm/action-setup@v2
        with:
          version: 8

      - name: Install dependencies
        run: pnpm install

      - name: Setup database
        run: |
          pnpm prisma generate
          pnpm prisma db push
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test

      - name: Run integration tests
        run: pnpm test:integration
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test

  e2e-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Setup pnpm
        uses: pnpm/action-setup@v2
        with:
          version: 8

      - name: Install dependencies
        run: pnpm install

      - name: Install Playwright Browsers
        run: npx playwright install --with-deps

      - name: Run E2E tests
        run: pnpm test:e2e

      - name: Upload Playwright Report
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 30
```

#### Coverage Badge:

```markdown
<!-- README.md -->

[![codecov](https://codecov.io/gh/yourusername/napiatke/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/napiatke)
[![Tests](https://github.com/yourusername/napiatke/workflows/Test%20Suite/badge.svg)](https://github.com/yourusername/napiatke/actions)
```

**Validation**:

- CI/CD pipeline running on every push
- Coverage reports generated and uploaded
- Test results visible in PR checks
- Badges displaying current status

---

## ✅ SPRINT COMPLETION CHECKLIST

### Testing Infrastructure

- [ ] Vitest configured and running
- [ ] Playwright installed and configured
- [ ] Test helpers and utilities created
- [ ] Mock data and fixtures prepared

### Unit Tests

- [ ] Service tests written (>80% coverage)
- [ ] Utility function tests written
- [ ] Hook tests written
- [ ] Component tests written

### Integration Tests

- [ ] tRPC router tests written
- [ ] Database integration tests written
- [ ] Authorization tests written
- [ ] API endpoint tests written

### E2E Tests

- [ ] Critical user flows tested
- [ ] Cross-browser testing passed
- [ ] Mobile responsive tests passed
- [ ] Screenshot/video capture configured

### Performance Tests

- [ ] Load tests written and executed
- [ ] Performance metrics collected
- [ ] Bottlenecks identified and fixed
- [ ] Web Vitals monitored

### CI/CD Integration

- [ ] GitHub Actions workflow configured
- [ ] Tests running on every PR
- [ ] Coverage reports generated
- [ ] Coverage thresholds enforced
- [ ] Badges added to README

---

## 📊 SUCCESS METRICS

- **Code Coverage**: >80% (lines, functions, branches)
- **Test Count**: 150+ tests across all types
- **CI/CD**: All tests passing on main branch
- **Performance**: p95 response time <500ms under load
- **E2E Success Rate**: >95% pass rate

---

**Sprint Completion**: All 5 tasks completed and validated ✅
**Next Sprint**: 12.2 - Documentation (Tasks 148-152)
**Quality**: Production-ready with comprehensive test coverage
