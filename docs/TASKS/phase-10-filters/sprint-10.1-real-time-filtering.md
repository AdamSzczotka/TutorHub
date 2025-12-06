# Phase 10 - Sprint 10.1: Real-Time Filtering

## Tasks 123-127: Advanced Filtering System Implementation

> **Duration**: Week 14 (First half of Phase 10)
> **Goal**: Implement real-time filtering with URL persistence, debounced search, and advanced filter combinations
> **Dependencies**: Phase 1-9 completed (All core features operational)

---

## 📋 SPRINT OVERVIEW

| Task ID | Description                   | Priority | Estimated Time | Dependencies     |
| ------- | ----------------------------- | -------- | -------------- | ---------------- |
| 123     | Alpine.js filter components   | Critical | 6h             | Phase 9 complete |
| 124     | URL persistence system        | Critical | 4h             | Task 123         |
| 125     | Debounced search (300ms)      | Critical | 5h             | Task 124         |
| 126     | Filter combinations & presets | High     | 7h             | Task 125         |
| 127     | Advanced date range picker    | High     | 6h             | Task 126         |

**Total Estimated Time**: 28 hours

---

## 🎯 DETAILED TASK BREAKDOWN

### Task 123: Alpine.js Filter Components

**Files**: `components/features/filters/FilterDropdown.tsx`, `components/features/filters/MultiSelect.tsx`, `lib/alpine-setup.ts`
**Reference**: DevelopmentRoadmap.md task 123

#### Alpine.js Setup:

```bash
pnpm add alpinejs@3.14.1
pnpm add @types/alpinejs -D
```

#### Filter Dropdown Component:

```typescript
// components/features/filters/FilterDropdown.tsx
'use client';

import { useState, useEffect } from 'react';
import { Button } from '~/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from '~/components/ui/dropdown-menu';
import { Badge } from '~/components/ui/badge';
import { ChevronDown, X } from 'lucide-react';

interface FilterOption {
  value: string;
  label: string;
  count?: number;
}

interface FilterDropdownProps {
  label: string;
  options: FilterOption[];
  value: string | null;
  onChange: (value: string | null) => void;
  icon?: React.ReactNode;
  clearable?: boolean;
}

export function FilterDropdown({
  label,
  options,
  value,
  onChange,
  icon,
  clearable = true,
}: FilterDropdownProps) {
  const selectedOption = options.find((opt) => opt.value === value);

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation();
    onChange(null);
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant={value ? 'default' : 'outline'}
          className="flex items-center space-x-2"
        >
          {icon}
          <span>{selectedOption?.label || label}</span>
          {value && clearable && (
            <X
              className="h-4 w-4 ml-2 hover:text-red-500"
              onClick={handleClear}
            />
          )}
          <ChevronDown className="h-4 w-4 ml-1" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-56">
        {options.map((option) => (
          <DropdownMenuItem
            key={option.value}
            onClick={() => onChange(option.value)}
            className="flex items-center justify-between"
          >
            <span>{option.label}</span>
            {option.count !== undefined && (
              <Badge variant="secondary" className="ml-2">
                {option.count}
              </Badge>
            )}
          </DropdownMenuItem>
        ))}
        {clearable && value && (
          <>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => onChange(null)}>
              <X className="h-4 w-4 mr-2" />
              Wyczyść filtr
            </DropdownMenuItem>
          </>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
```

#### Multi-Select Component:

```typescript
// components/features/filters/MultiSelect.tsx
'use client';

import { useState } from 'react';
import { Button } from '~/components/ui/button';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '~/components/ui/popover';
import { Checkbox } from '~/components/ui/checkbox';
import { Badge } from '~/components/ui/badge';
import { ChevronDown, X } from 'lucide-react';
import { ScrollArea } from '~/components/ui/scroll-area';

interface MultiSelectOption {
  value: string;
  label: string;
  count?: number;
}

interface MultiSelectProps {
  label: string;
  options: MultiSelectOption[];
  value: string[];
  onChange: (value: string[]) => void;
  icon?: React.ReactNode;
  maxDisplay?: number;
}

export function MultiSelect({
  label,
  options,
  value,
  onChange,
  icon,
  maxDisplay = 2,
}: MultiSelectProps) {
  const [open, setOpen] = useState(false);

  const handleToggle = (optionValue: string) => {
    if (value.includes(optionValue)) {
      onChange(value.filter((v) => v !== optionValue));
    } else {
      onChange([...value, optionValue]);
    }
  };

  const handleClearAll = () => {
    onChange([]);
  };

  const selectedLabels = options
    .filter((opt) => value.includes(opt.value))
    .map((opt) => opt.label);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant={value.length > 0 ? 'default' : 'outline'}
          className="flex items-center space-x-2"
        >
          {icon}
          <span>
            {value.length === 0
              ? label
              : selectedLabels.slice(0, maxDisplay).join(', ')}
          </span>
          {value.length > maxDisplay && (
            <Badge variant="secondary" className="ml-1">
              +{value.length - maxDisplay}
            </Badge>
          )}
          <ChevronDown className="h-4 w-4 ml-1" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-64 p-0" align="start">
        <div className="p-3 border-b flex items-center justify-between">
          <span className="font-medium text-sm">{label}</span>
          {value.length > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleClearAll}
              className="h-6 px-2"
            >
              <X className="h-3 w-3 mr-1" />
              Wyczyść
            </Button>
          )}
        </div>
        <ScrollArea className="h-64">
          <div className="p-2 space-y-1">
            {options.map((option) => (
              <div
                key={option.value}
                className="flex items-center space-x-2 p-2 hover:bg-gray-100 rounded cursor-pointer"
                onClick={() => handleToggle(option.value)}
              >
                <Checkbox
                  checked={value.includes(option.value)}
                  onCheckedChange={() => handleToggle(option.value)}
                />
                <span className="flex-1 text-sm">{option.label}</span>
                {option.count !== undefined && (
                  <Badge variant="outline" className="text-xs">
                    {option.count}
                  </Badge>
                )}
              </div>
            ))}
          </div>
        </ScrollArea>
        <div className="p-2 border-t bg-gray-50">
          <div className="text-xs text-gray-600">
            Wybrano: {value.length} / {options.length}
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}
```

#### Clear All Filters Component:

```typescript
// components/features/filters/ClearFilters.tsx
import { Button } from '~/components/ui/button';
import { X } from 'lucide-react';

interface ClearFiltersProps {
  hasActiveFilters: boolean;
  onClear: () => void;
}

export function ClearFilters({ hasActiveFilters, onClear }: ClearFiltersProps) {
  if (!hasActiveFilters) return null;

  return (
    <Button variant="ghost" size="sm" onClick={onClear} className="text-red-500">
      <X className="h-4 w-4 mr-1" />
      Wyczyść wszystkie filtry
    </Button>
  );
}
```

**Validation**:

- All filter components render correctly
- Multi-select handles multiple selections
- Clear functionality works for individual and all filters
- Responsive design on mobile

---

### Task 124: URL Persistence System

**Files**: `lib/hooks/useUrlFilters.ts`, `lib/utils/url-params.ts`
**Reference**: DevelopmentRoadmap.md task 124

#### URL Persistence Hook:

```typescript
// lib/hooks/useUrlFilters.ts
'use client';

import { useRouter, useSearchParams, usePathname } from 'next/navigation';
import { useCallback, useMemo } from 'react';

export interface FilterState {
  [key: string]: string | string[] | null;
}

export function useUrlFilters() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  // Parse current filters from URL
  const filters = useMemo((): FilterState => {
    const result: FilterState = {};
    searchParams.forEach((value, key) => {
      if (value.includes(',')) {
        result[key] = value.split(',');
      } else {
        result[key] = value;
      }
    });
    return result;
  }, [searchParams]);

  // Update filters in URL
  const setFilters = useCallback(
    (newFilters: FilterState) => {
      const params = new URLSearchParams();

      Object.entries(newFilters).forEach(([key, value]) => {
        if (value === null || value === undefined) {
          // Skip null/undefined values
          return;
        }

        if (Array.isArray(value)) {
          if (value.length > 0) {
            params.set(key, value.join(','));
          }
        } else if (value !== '') {
          params.set(key, value);
        }
      });

      const queryString = params.toString();
      const url = queryString ? `${pathname}?${queryString}` : pathname;

      router.push(url, { scroll: false });
    },
    [pathname, router]
  );

  // Update single filter
  const setFilter = useCallback(
    (key: string, value: string | string[] | null) => {
      setFilters({ ...filters, [key]: value });
    },
    [filters, setFilters]
  );

  // Clear all filters
  const clearFilters = useCallback(() => {
    router.push(pathname, { scroll: false });
  }, [pathname, router]);

  // Clear single filter
  const clearFilter = useCallback(
    (key: string) => {
      const newFilters = { ...filters };
      delete newFilters[key];
      setFilters(newFilters);
    },
    [filters, setFilters]
  );

  // Check if any filters are active
  const hasActiveFilters = useMemo(() => {
    return Object.keys(filters).length > 0;
  }, [filters]);

  return {
    filters,
    setFilters,
    setFilter,
    clearFilters,
    clearFilter,
    hasActiveFilters,
  };
}
```

#### URL Params Utility:

```typescript
// lib/utils/url-params.ts
export function encodeFiltersToUrl(filters: Record<string, any>): string {
  const params = new URLSearchParams();

  Object.entries(filters).forEach(([key, value]) => {
    if (value === null || value === undefined || value === '') {
      return;
    }

    if (Array.isArray(value)) {
      if (value.length > 0) {
        params.set(key, value.join(','));
      }
    } else if (value instanceof Date) {
      params.set(key, value.toISOString());
    } else {
      params.set(key, String(value));
    }
  });

  return params.toString();
}

export function decodeFiltersFromUrl(
  searchParams: URLSearchParams
): Record<string, any> {
  const filters: Record<string, any> = {};

  searchParams.forEach((value, key) => {
    // Handle comma-separated arrays
    if (value.includes(',')) {
      filters[key] = value.split(',');
    }
    // Handle dates
    else if (key.includes('Date') || key.includes('_at')) {
      const date = new Date(value);
      if (!isNaN(date.getTime())) {
        filters[key] = date;
      }
    }
    // Handle booleans
    else if (value === 'true' || value === 'false') {
      filters[key] = value === 'true';
    }
    // Handle regular strings
    else {
      filters[key] = value;
    }
  });

  return filters;
}

export function createShareableUrl(
  baseUrl: string,
  filters: Record<string, any>
): string {
  const encoded = encodeFiltersToUrl(filters);
  return encoded ? `${baseUrl}?${encoded}` : baseUrl;
}
```

#### Shareable URL Component:

```typescript
// components/features/filters/ShareableUrl.tsx
'use client';

import { useState } from 'react';
import { Button } from '~/components/ui/button';
import { Input } from '~/components/ui/input';
import { Share2, Check, Copy } from 'lucide-react';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '~/components/ui/popover';
import { useToast } from '~/hooks/use-toast';

export function ShareableUrl() {
  const [copied, setCopied] = useState(false);
  const { toast } = useToast();
  const shareUrl = typeof window !== 'undefined' ? window.location.href : '';

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      toast({ title: 'Link skopiowany do schowka!' });
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      toast({
        title: 'Błąd',
        description: 'Nie udało się skopiować linku',
        variant: 'destructive',
      });
    }
  };

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="outline" size="sm">
          <Share2 className="h-4 w-4 mr-2" />
          Udostępnij
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-80">
        <div className="space-y-2">
          <h4 className="font-medium text-sm">Link z filtrami</h4>
          <p className="text-xs text-gray-600">
            Skopiuj poniższy link, aby udostępnić bieżące filtry
          </p>
          <div className="flex items-center space-x-2">
            <Input value={shareUrl} readOnly className="text-xs" />
            <Button size="sm" onClick={handleCopy} variant="secondary">
              {copied ? (
                <Check className="h-4 w-4 text-green-500" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}
```

**Validation**:

- URL updates on filter changes
- Browser back/forward navigation works
- Shareable URLs maintain filter state
- No infinite loops or unnecessary re-renders

---

### Task 125: Debounced Search (300ms)

**Files**: `lib/hooks/useDebouncedSearch.ts`, `components/features/filters/SearchInput.tsx`
**Reference**: DevelopmentRoadmap.md task 125

#### Debounced Search Hook:

```typescript
// lib/hooks/useDebouncedSearch.ts
'use client';

import { useState, useEffect, useCallback } from 'react';

export function useDebouncedSearch(
  initialValue: string = '',
  delay: number = 300
) {
  const [value, setValue] = useState(initialValue);
  const [debouncedValue, setDebouncedValue] = useState(initialValue);
  const [isDebouncing, setIsDebouncing] = useState(false);

  useEffect(() => {
    setIsDebouncing(true);
    const handler = setTimeout(() => {
      setDebouncedValue(value);
      setIsDebouncing(false);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  const reset = useCallback(() => {
    setValue('');
    setDebouncedValue('');
    setIsDebouncing(false);
  }, []);

  return {
    value,
    debouncedValue,
    isDebouncing,
    setValue,
    reset,
  };
}
```

#### Search Input Component:

```typescript
// components/features/filters/SearchInput.tsx
'use client';

import { Input } from '~/components/ui/input';
import { Search, X, Loader2 } from 'lucide-react';
import { Button } from '~/components/ui/button';
import { useDebouncedSearch } from '~/lib/hooks/useDebouncedSearch';
import { useEffect } from 'react';

interface SearchInputProps {
  placeholder?: string;
  onSearch: (value: string) => void;
  initialValue?: string;
  className?: string;
}

export function SearchInput({
  placeholder = 'Szukaj...',
  onSearch,
  initialValue = '',
  className = '',
}: SearchInputProps) {
  const { value, debouncedValue, isDebouncing, setValue, reset } =
    useDebouncedSearch(initialValue, 300);

  useEffect(() => {
    onSearch(debouncedValue);
  }, [debouncedValue, onSearch]);

  return (
    <div className={`relative ${className}`}>
      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
      <Input
        type="text"
        placeholder={placeholder}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        className="pl-10 pr-20"
      />
      <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex items-center space-x-1">
        {isDebouncing && (
          <Loader2 className="h-4 w-4 text-gray-400 animate-spin" />
        )}
        {value && (
          <Button
            variant="ghost"
            size="sm"
            onClick={reset}
            className="h-6 w-6 p-0"
          >
            <X className="h-4 w-4" />
          </Button>
        )}
      </div>
    </div>
  );
}
```

#### Advanced Search with Cancel:

```typescript
// lib/hooks/useAbortableSearch.ts
'use client';

import { useRef, useCallback } from 'react';

export function useAbortableSearch<T>(
  searchFn: (query: string, signal: AbortSignal) => Promise<T>
) {
  const abortControllerRef = useRef<AbortController | null>(null);

  const search = useCallback(
    async (query: string): Promise<T | null> => {
      // Cancel previous request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      // Create new abort controller
      abortControllerRef.current = new AbortController();

      try {
        const result = await searchFn(query, abortControllerRef.current.signal);
        return result;
      } catch (error: any) {
        if (error.name === 'AbortError') {
          console.log('Search cancelled');
          return null;
        }
        throw error;
      }
    },
    [searchFn]
  );

  const cancel = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
  }, []);

  return { search, cancel };
}
```

#### Search with Loading States:

```typescript
// components/features/filters/AdvancedSearch.tsx
'use client';

import { useState, useCallback } from 'react';
import { SearchInput } from './SearchInput';
import { useDebouncedSearch } from '~/lib/hooks/useDebouncedSearch';
import { useAbortableSearch } from '~/lib/hooks/useAbortableSearch';
import { api } from '~/utils/api';
import { Loader2 } from 'lucide-react';

interface AdvancedSearchProps {
  onResultsChange: (results: any[]) => void;
  searchType: 'students' | 'events' | 'tutors';
}

export function AdvancedSearch({
  onResultsChange,
  searchType,
}: AdvancedSearchProps) {
  const [isSearching, setIsSearching] = useState(false);
  const { value, debouncedValue, setValue } = useDebouncedSearch('', 300);

  const searchFn = useCallback(
    async (query: string, signal: AbortSignal) => {
      if (!query) {
        return [];
      }

      setIsSearching(true);

      try {
        // Example: search based on type
        let results;
        if (searchType === 'students') {
          results = await api.student.search.query({ query }, { signal } as any);
        } else if (searchType === 'events') {
          results = await api.event.search.query({ query }, { signal } as any);
        } else {
          results = await api.user.searchTutors.query(
            { query },
            { signal } as any
          );
        }

        return results;
      } finally {
        setIsSearching(false);
      }
    },
    [searchType]
  );

  const { search, cancel } = useAbortableSearch(searchFn);

  const handleSearch = useCallback(
    async (query: string) => {
      const results = await search(query);
      if (results) {
        onResultsChange(results);
      }
    },
    [search, onResultsChange]
  );

  return (
    <div className="relative">
      <SearchInput
        placeholder={`Szukaj ${searchType === 'students' ? 'uczniów' : searchType === 'events' ? 'zajęć' : 'korepetytorów'}...`}
        onSearch={handleSearch}
        initialValue={value}
      />
      {isSearching && (
        <div className="absolute right-12 top-1/2 transform -translate-y-1/2">
          <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />
        </div>
      )}
    </div>
  );
}
```

**Validation**:

- 300ms debounce working correctly
- Loading indicators during search
- Request cancellation on new input
- No race conditions

---

### Task 126: Filter Combinations & Presets

**Files**: `components/features/filters/FilterPresets.tsx`, `lib/validations/filter-preset.ts`, `server/api/routers/filterPreset.ts`
**Reference**: DevelopmentRoadmap.md task 126

#### Filter Preset Schema:

```typescript
// lib/validations/filter-preset.ts
import { z } from 'zod';

export const filterPresetSchema = z.object({
  id: z.string().uuid().optional(),
  name: z.string().min(1, 'Nazwa jest wymagana').max(50),
  description: z.string().max(200).optional(),
  filters: z.record(z.any()),
  isPublic: z.boolean().default(false),
  userId: z.string().uuid(),
  createdAt: z.date().optional(),
  updatedAt: z.date().optional(),
});

export type FilterPreset = z.infer<typeof filterPresetSchema>;

export const createFilterPresetSchema = filterPresetSchema.omit({
  id: true,
  createdAt: true,
  updatedAt: true,
});

export const updateFilterPresetSchema = filterPresetSchema
  .partial()
  .required({ id: true });
```

#### Filter Presets Component:

```typescript
// components/features/filters/FilterPresets.tsx
'use client';

import { useState } from 'react';
import { Button } from '~/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '~/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '~/components/ui/dialog';
import { Input } from '~/components/ui/input';
import { Textarea } from '~/components/ui/textarea';
import { Checkbox } from '~/components/ui/checkbox';
import { Star, Plus, Trash2 } from 'lucide-react';
import { api } from '~/utils/api';
import { useToast } from '~/hooks/use-toast';
import type { FilterState } from '~/lib/hooks/useUrlFilters';

interface FilterPresetsProps {
  currentFilters: FilterState;
  onApplyPreset: (filters: FilterState) => void;
}

export function FilterPresets({
  currentFilters,
  onApplyPreset,
}: FilterPresetsProps) {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [presetName, setPresetName] = useState('');
  const [presetDescription, setPresetDescription] = useState('');
  const [isPublic, setIsPublic] = useState(false);
  const { toast } = useToast();
  const utils = api.useUtils();

  // Fetch presets
  const { data: presets } = api.filterPreset.getAll.useQuery();

  // Mutations
  const createPreset = api.filterPreset.create.useMutation({
    onSuccess: () => {
      utils.filterPreset.getAll.invalidate();
      toast({ title: 'Preset zapisany!' });
      setIsDialogOpen(false);
      setPresetName('');
      setPresetDescription('');
      setIsPublic(false);
    },
    onError: (error) => {
      toast({
        title: 'Błąd',
        description: error.message,
        variant: 'destructive',
      });
    },
  });

  const deletePreset = api.filterPreset.delete.useMutation({
    onSuccess: () => {
      utils.filterPreset.getAll.invalidate();
      toast({ title: 'Preset usunięty' });
    },
  });

  const handleSavePreset = () => {
    if (!presetName) {
      toast({
        title: 'Błąd',
        description: 'Podaj nazwę presetu',
        variant: 'destructive',
      });
      return;
    }

    createPreset.mutate({
      name: presetName,
      description: presetDescription,
      filters: currentFilters,
      isPublic,
    });
  };

  const handleApplyPreset = (presetId: string) => {
    const preset = presets?.find((p) => p.id === presetId);
    if (preset) {
      onApplyPreset(preset.filters as FilterState);
      toast({ title: `Zastosowano preset: ${preset.name}` });
    }
  };

  const handleDeletePreset = (presetId: string) => {
    if (confirm('Czy na pewno chcesz usunąć ten preset?')) {
      deletePreset.mutate({ id: presetId });
    }
  };

  const hasActiveFilters = Object.keys(currentFilters).length > 0;

  return (
    <div className="flex items-center space-x-2">
      <Select onValueChange={handleApplyPreset}>
        <SelectTrigger className="w-48">
          <SelectValue placeholder="Wybierz preset" />
        </SelectTrigger>
        <SelectContent>
          {presets?.map((preset) => (
            <SelectItem key={preset.id} value={preset.id}>
              <div className="flex items-center justify-between w-full">
                <span>{preset.name}</span>
                {preset.isPublic && (
                  <Star className="h-3 w-3 ml-2 text-yellow-500" />
                )}
              </div>
            </SelectItem>
          ))}
          {!presets?.length && (
            <div className="p-2 text-sm text-gray-500">Brak zapisanych presetów</div>
          )}
        </SelectContent>
      </Select>

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogTrigger asChild>
          <Button
            variant="outline"
            size="sm"
            disabled={!hasActiveFilters}
            title={!hasActiveFilters ? 'Najpierw zastosuj filtry' : 'Zapisz jako preset'}
          >
            <Plus className="h-4 w-4 mr-1" />
            Zapisz
          </Button>
        </DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Zapisz preset filtrów</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Nazwa</label>
              <Input
                value={presetName}
                onChange={(e) => setPresetName(e.target.value)}
                placeholder="np. Zajęcia z matematyki w tym miesiącu"
              />
            </div>
            <div>
              <label className="text-sm font-medium">Opis (opcjonalnie)</label>
              <Textarea
                value={presetDescription}
                onChange={(e) => setPresetDescription(e.target.value)}
                placeholder="Krótki opis presetu..."
                rows={3}
              />
            </div>
            <div className="flex items-center space-x-2">
              <Checkbox
                checked={isPublic}
                onCheckedChange={(checked) => setIsPublic(checked as boolean)}
              />
              <label className="text-sm">
                Udostępnij innym użytkownikom (publiczny)
              </label>
            </div>
            <div className="flex justify-end space-x-2">
              <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
                Anuluj
              </Button>
              <Button onClick={handleSavePreset}>Zapisz preset</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
```

#### Quick Filters Component:

```typescript
// components/features/filters/QuickFilters.tsx
import { Button } from '~/components/ui/button';
import { Calendar, Clock, Users } from 'lucide-react';
import type { FilterState } from '~/lib/hooks/useUrlFilters';

interface QuickFiltersProps {
  onApply: (filters: FilterState) => void;
}

export function QuickFilters({ onApply }: QuickFiltersProps) {
  const quickFilters = [
    {
      label: 'Dzisiaj',
      icon: Calendar,
      filters: {
        startDate: new Date().toISOString().split('T')[0],
        endDate: new Date().toISOString().split('T')[0],
      },
    },
    {
      label: 'Ten tydzień',
      icon: Clock,
      filters: {
        startDate: getStartOfWeek().toISOString().split('T')[0],
        endDate: getEndOfWeek().toISOString().split('T')[0],
      },
    },
    {
      label: 'Zajęcia grupowe',
      icon: Users,
      filters: {
        isGroupLesson: 'true',
      },
    },
  ];

  return (
    <div className="flex flex-wrap gap-2">
      <span className="text-sm font-medium text-gray-600 mr-2">Szybkie filtry:</span>
      {quickFilters.map((filter) => {
        const Icon = filter.icon;
        return (
          <Button
            key={filter.label}
            variant="outline"
            size="sm"
            onClick={() => onApply(filter.filters)}
            className="flex items-center space-x-1"
          >
            <Icon className="h-3 w-3" />
            <span>{filter.label}</span>
          </Button>
        );
      })}
    </div>
  );
}

function getStartOfWeek(): Date {
  const now = new Date();
  const day = now.getDay();
  const diff = now.getDate() - day + (day === 0 ? -6 : 1); // Monday
  return new Date(now.setDate(diff));
}

function getEndOfWeek(): Date {
  const start = getStartOfWeek();
  const end = new Date(start);
  end.setDate(start.getDate() + 6);
  return end;
}
```

**Validation**:

- Filter presets save and load correctly
- Public/private preset functionality works
- Quick filters apply correctly
- Preset deletion requires confirmation

---

### Task 127: Advanced Date Range Picker

**Files**: `components/features/filters/DateRangePicker.tsx`, `lib/utils/date-presets.ts`
**Reference**: DevelopmentRoadmap.md task 127

#### Date Range Picker Component:

```typescript
// components/features/filters/DateRangePicker.tsx
'use client';

import { useState } from 'react';
import { Button } from '~/components/ui/button';
import { Calendar } from '~/components/ui/calendar';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '~/components/ui/popover';
import { CalendarIcon, X } from 'lucide-react';
import { format, isValid } from 'date-fns';
import { pl } from 'date-fns/locale';
import type { DateRange } from 'react-day-picker';

interface DateRangePickerProps {
  value: DateRange | undefined;
  onChange: (range: DateRange | undefined) => void;
  placeholder?: string;
  presets?: { label: string; range: DateRange }[];
}

export function DateRangePicker({
  value,
  onChange,
  placeholder = 'Wybierz zakres dat',
  presets,
}: DateRangePickerProps) {
  const [open, setOpen] = useState(false);

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation();
    onChange(undefined);
  };

  const formatDateRange = (range: DateRange | undefined): string => {
    if (!range?.from) return placeholder;

    if (range.to) {
      return `${format(range.from, 'dd MMM yyyy', { locale: pl })} - ${format(range.to, 'dd MMM yyyy', { locale: pl })}`;
    }

    return format(range.from, 'dd MMM yyyy', { locale: pl });
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant={value?.from ? 'default' : 'outline'}
          className="flex items-center space-x-2 justify-start text-left font-normal"
        >
          <CalendarIcon className="h-4 w-4" />
          <span className="flex-1">{formatDateRange(value)}</span>
          {value?.from && (
            <X
              className="h-4 w-4 hover:text-red-500"
              onClick={handleClear}
            />
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0" align="start">
        <div className="flex">
          {presets && (
            <div className="border-r p-3 space-y-1 w-36">
              <div className="text-xs font-medium text-gray-600 mb-2">
                Szybki wybór
              </div>
              {presets.map((preset) => (
                <Button
                  key={preset.label}
                  variant="ghost"
                  size="sm"
                  className="w-full justify-start text-xs"
                  onClick={() => {
                    onChange(preset.range);
                    setOpen(false);
                  }}
                >
                  {preset.label}
                </Button>
              ))}
            </div>
          )}
          <div className="p-3">
            <Calendar
              mode="range"
              selected={value}
              onSelect={onChange}
              numberOfMonths={2}
              locale={pl}
              defaultMonth={value?.from}
            />
          </div>
        </div>
        <div className="border-t p-2 flex justify-between">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onChange(undefined)}
          >
            Wyczyść
          </Button>
          <Button size="sm" onClick={() => setOpen(false)}>
            Zastosuj
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  );
}
```

#### Date Presets Utility:

```typescript
// lib/utils/date-presets.ts
import {
  startOfDay,
  endOfDay,
  subDays,
  startOfWeek,
  endOfWeek,
  startOfMonth,
  endOfMonth,
  subMonths,
  addMonths,
} from 'date-fns';
import type { DateRange } from 'react-day-picker';

export const DATE_PRESETS: { label: string; range: DateRange }[] = [
  {
    label: 'Dzisiaj',
    range: {
      from: startOfDay(new Date()),
      to: endOfDay(new Date()),
    },
  },
  {
    label: 'Wczoraj',
    range: {
      from: startOfDay(subDays(new Date(), 1)),
      to: endOfDay(subDays(new Date(), 1)),
    },
  },
  {
    label: 'Ostatnie 7 dni',
    range: {
      from: startOfDay(subDays(new Date(), 6)),
      to: endOfDay(new Date()),
    },
  },
  {
    label: 'Ostatnie 30 dni',
    range: {
      from: startOfDay(subDays(new Date(), 29)),
      to: endOfDay(new Date()),
    },
  },
  {
    label: 'Ten tydzień',
    range: {
      from: startOfWeek(new Date(), { weekStartsOn: 1 }),
      to: endOfWeek(new Date(), { weekStartsOn: 1 }),
    },
  },
  {
    label: 'Ten miesiąc',
    range: {
      from: startOfMonth(new Date()),
      to: endOfMonth(new Date()),
    },
  },
  {
    label: 'Poprzedni miesiąc',
    range: {
      from: startOfMonth(subMonths(new Date(), 1)),
      to: endOfMonth(subMonths(new Date(), 1)),
    },
  },
  {
    label: 'Następny miesiąc',
    range: {
      from: startOfMonth(addMonths(new Date(), 1)),
      to: endOfMonth(addMonths(new Date(), 1)),
    },
  },
];

export function isDateInRange(
  date: Date,
  range: DateRange | undefined
): boolean {
  if (!range?.from) return true;
  if (!range.to) return date >= range.from;
  return date >= range.from && date <= range.to;
}
```

#### Timezone Handler:

```typescript
// lib/utils/timezone.ts
import { toZonedTime, fromZonedTime } from 'date-fns-tz';

const TIMEZONE = 'Europe/Warsaw';

export function toLocalTime(date: Date): Date {
  return toZonedTime(date, TIMEZONE);
}

export function toUTCTime(date: Date): Date {
  return fromZonedTime(date, TIMEZONE);
}

export function formatDateWithTimezone(
  date: Date,
  formatStr: string = 'yyyy-MM-dd HH:mm:ss'
): string {
  const zonedDate = toLocalTime(date);
  return format(zonedDate, formatStr);
}

export function getCurrentTimezone(): string {
  return TIMEZONE;
}
```

**Validation**:

- Date range picker displays correctly
- Presets apply correct date ranges
- Timezone handling accurate for Poland (Europe/Warsaw)
- Clear functionality works
- Two-month calendar view functional

---

## ✅ SPRINT COMPLETION CHECKLIST

### Technical Validation

- [ ] Alpine.js components integrated
- [ ] Filter dropdowns working correctly
- [ ] Multi-select functionality operational
- [ ] URL persistence active
- [ ] Debounced search (300ms) working
- [ ] Request cancellation functional
- [ ] Filter presets save/load correctly
- [ ] Date range picker fully functional
- [ ] Timezone handling accurate

### Feature Validation

- [ ] All filter types (dropdown, multi-select, search) work
- [ ] URL updates on filter changes
- [ ] Shareable URLs maintain state
- [ ] Search debouncing prevents excessive requests
- [ ] Filter combinations can be saved as presets
- [ ] Quick filters apply correctly
- [ ] Date presets work as expected
- [ ] Clear filters functionality complete

### Integration Testing

- [ ] tRPC API integration successful
- [ ] Filter state persists across navigation
- [ ] No memory leaks from debounce/subscriptions
- [ ] Performance optimized for large datasets

### Performance

- [ ] Filter operations smooth (<100ms)
- [ ] Search debounce exactly 300ms
- [ ] URL updates don't cause page reload
- [ ] Date picker renders quickly

---

## 📊 SUCCESS METRICS

- **User Experience**: Intuitive filtering with instant feedback
- **Performance**: <100ms filter application, 300ms search debounce
- **Functionality**: 100% of filtering features operational
- **Persistence**: URL state preservation working flawlessly
- **Mobile**: Fully responsive filter controls

---

**Sprint Completion**: All 5 tasks completed and validated ✅
**Next Sprint**: 10.2 - Data Export (Tasks 128-132)
**Integration**: Filter system ready for all data tables and views
