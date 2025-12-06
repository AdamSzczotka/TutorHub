# Phase 2 - Sprint 2.4: CMS Admin Panel

## Tasks 044H-044N: Content Management System

> **Duration**: Week 5, Days 4-5 (2 dni)
> **Goal**: Full CMS in admin panel for managing landing page content
> **Dependencies**: Sprint 2.3 complete

---

## 📋 SPRINT OVERVIEW

| Task ID | Description                 | Priority | Estimated Time | Dependencies |
| ------- | --------------------------- | -------- | -------------- | ------------ |
| 044H    | CMS router & service        | Critical | 5h             | Sprint 2.3   |
| 044I    | Content editor (rich text)  | Critical | 4h             | Task 044H    |
| 044J    | Team members management     | High     | 5h             | Task 044H    |
| 044K    | Testimonials moderation     | High     | 4h             | Task 044H    |
| 044L    | Pricing editor              | Medium   | 3h             | Task 044H    |
| 044M    | School settings             | High     | 4h             | Task 044H    |
| 044N    | Google Maps API integration | High     | 5h             | Task 044H    |

**Total Estimated Time**: 30 hours

---

## 🎯 DETAILED TASK BREAKDOWN

### Task 044H: CMS Router & Service

**Files**:

- `server/api/routers/cms.ts`
- `server/services/cms/contentService.ts`
- `lib/validations/cms.ts`
- `prisma/schema.prisma` (additions)

#### Prisma Schema Extensions:

```prisma
// Add to schema.prisma

model LandingPageContent {
  id          String   @id @default(uuid())
  section     String   @unique // 'hero', 'about', 'features', 'cta'
  title       String?
  subtitle    String?
  content     Json?    // Rich text content
  imageUrl    String?
  buttonText  String?
  buttonUrl   String?
  isPublished Boolean  @default(true)

  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  @@index([section])
  @@map("landing_page_content")
}

model TeamMember {
  id          String   @id @default(uuid())
  name        String
  surname     String
  position    String
  bio         String?
  imageUrl    String?
  linkedIn    String?
  email       String?
  phone       String?
  displayOrder Int     @default(0)
  isVisible   Boolean  @default(true)

  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  @@index([displayOrder])
  @@index([isVisible])
  @@map("team_members")
}

model Testimonial {
  id           String   @id @default(uuid())
  authorName   String
  authorRole   String? // 'student', 'parent', 'tutor'
  content      String
  rating       Int      @default(5) // 1-5
  imageUrl     String?
  isApproved   Boolean  @default(false)
  isPublished  Boolean  @default(false)
  submittedAt  DateTime @default(now())
  approvedAt   DateTime?
  approvedBy   String?
  displayOrder Int      @default(0)

  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  @@index([isApproved])
  @@index([isPublished])
  @@index([displayOrder])
  @@map("testimonials")
}

model PricingPlan {
  id              String   @id @default(uuid())
  name            String
  description     String?
  price           Decimal  @db.Decimal(8, 2)
  priceUnit       String   @default("zł/h") // 'zł/h', 'zł/miesiąc'
  features        Json     // Array of feature strings
  isPopular       Boolean  @default(false)
  isVisible       Boolean  @default(true)
  displayOrder    Int      @default(0)
  subjectIds      String[] // Array of subject IDs
  levelIds        String[] // Array of level IDs

  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  @@index([isVisible])
  @@index([displayOrder])
  @@map("pricing_plans")
}

model SchoolSettings {
  id              String   @id @default(uuid())
  schoolName      String   @default("Na Piątkę")
  tagline         String?
  description     String?
  logoUrl         String?
  faviconUrl      String?

  // Contact
  email           String?
  phone           String?
  address         String?
  city            String?
  postalCode      String?
  country         String   @default("Polska")

  // Location
  latitude        Decimal? @db.Decimal(10, 8)
  longitude       Decimal? @db.Decimal(11, 8)
  googleMapsUrl   String?

  // Social Media
  facebook        String?
  instagram       String?
  linkedin        String?
  youtube         String?

  // Business
  nip             String?
  regon           String?
  krs             String?

  // Opening Hours
  openingHours    Json?    // { 'monday': '8:00-20:00', ... }

  updatedAt DateTime @updatedAt
  updatedBy String?

  @@map("school_settings")
}

model UploadedFile {
  id           String   @id @default(uuid())
  originalName String
  filename     String
  mimeType     String
  size         Int
  path         String
  url          String
  uploadedBy   String
  category     String   @default("general") // 'avatar', 'content', 'logo', 'team'

  createdAt DateTime @default(now())

  @@index([uploadedBy])
  @@index([category])
  @@map("uploaded_files")
}
```

#### Validation Schemas:

```typescript
// lib/validations/cms.ts
import { z } from 'zod';

// Landing Page Content
export const landingContentSchema = z.object({
  section: z.enum(['hero', 'about', 'features', 'cta']),
  title: z.string().max(200).optional(),
  subtitle: z.string().max(500).optional(),
  content: z.any().optional(), // Rich text JSON
  imageUrl: z.string().url().optional(),
  buttonText: z.string().max(50).optional(),
  buttonUrl: z.string().max(200).optional(),
  isPublished: z.boolean().default(true),
});

export const updateLandingContentSchema = landingContentSchema
  .partial()
  .extend({
    id: z.string().uuid(),
  });

// Team Members
export const teamMemberSchema = z.object({
  name: z.string().min(2, 'Imię jest wymagane').max(50),
  surname: z.string().min(2, 'Nazwisko jest wymagane').max(50),
  position: z.string().min(2, 'Stanowisko jest wymagane').max(100),
  bio: z.string().max(500).optional(),
  imageUrl: z.string().url().optional(),
  linkedIn: z.string().url().optional(),
  email: z.string().email().optional(),
  phone: z.string().min(9).max(15).optional(),
  displayOrder: z.number().int().min(0).default(0),
  isVisible: z.boolean().default(true),
});

export const updateTeamMemberSchema = teamMemberSchema.partial().extend({
  id: z.string().uuid(),
});

export const reorderTeamMembersSchema = z.object({
  members: z.array(
    z.object({
      id: z.string().uuid(),
      displayOrder: z.number().int().min(0),
    })
  ),
});

// Testimonials
export const testimonialSchema = z.object({
  authorName: z.string().min(2, 'Imię autora jest wymagane').max(100),
  authorRole: z.enum(['student', 'parent', 'tutor']).optional(),
  content: z.string().min(10, 'Treść opinii jest zbyt krótka').max(1000),
  rating: z.number().int().min(1).max(5).default(5),
  imageUrl: z.string().url().optional(),
  isApproved: z.boolean().default(false),
  isPublished: z.boolean().default(false),
  displayOrder: z.number().int().min(0).default(0),
});

export const updateTestimonialSchema = testimonialSchema.partial().extend({
  id: z.string().uuid(),
});

export const approveTestimonialSchema = z.object({
  id: z.string().uuid(),
  isApproved: z.boolean(),
  isPublished: z.boolean().optional(),
});

// Pricing Plans
export const pricingPlanSchema = z.object({
  name: z.string().min(2, 'Nazwa planu jest wymagana').max(100),
  description: z.string().max(500).optional(),
  price: z.number().positive('Cena musi być większa od 0'),
  priceUnit: z.string().default('zł/h'),
  features: z.array(z.string()).min(1, 'Dodaj przynajmniej jedną cechę'),
  isPopular: z.boolean().default(false),
  isVisible: z.boolean().default(true),
  displayOrder: z.number().int().min(0).default(0),
  subjectIds: z.array(z.string().uuid()).optional(),
  levelIds: z.array(z.string().uuid()).optional(),
});

export const updatePricingPlanSchema = pricingPlanSchema.partial().extend({
  id: z.string().uuid(),
});

// School Settings
export const schoolSettingsSchema = z.object({
  schoolName: z.string().min(2).max(100).default('Na Piątkę'),
  tagline: z.string().max(200).optional(),
  description: z.string().max(1000).optional(),
  logoUrl: z.string().url().optional(),
  faviconUrl: z.string().url().optional(),

  email: z.string().email().optional(),
  phone: z.string().min(9).max(15).optional(),
  address: z.string().max(200).optional(),
  city: z.string().max(100).optional(),
  postalCode: z.string().max(10).optional(),
  country: z.string().default('Polska'),

  latitude: z.number().min(-90).max(90).optional(),
  longitude: z.number().min(-180).max(180).optional(),
  googleMapsUrl: z.string().url().optional(),

  facebook: z.string().url().optional(),
  instagram: z.string().url().optional(),
  linkedin: z.string().url().optional(),
  youtube: z.string().url().optional(),

  nip: z.string().max(20).optional(),
  regon: z.string().max(20).optional(),
  krs: z.string().max(20).optional(),

  openingHours: z.any().optional(), // JSON object
});

export const updateSchoolSettingsSchema = schoolSettingsSchema
  .partial()
  .extend({
    id: z.string().uuid(),
  });

// File Upload
export const uploadFileSchema = z.object({
  category: z
    .enum(['avatar', 'content', 'logo', 'team', 'general'])
    .default('general'),
});

export type LandingContentInput = z.infer<typeof landingContentSchema>;
export type TeamMemberInput = z.infer<typeof teamMemberSchema>;
export type TestimonialInput = z.infer<typeof testimonialSchema>;
export type PricingPlanInput = z.infer<typeof pricingPlanSchema>;
export type SchoolSettingsInput = z.infer<typeof schoolSettingsSchema>;
```

#### tRPC Router:

```typescript
// server/api/routers/cms.ts
import {
  createTRPCRouter,
  adminProcedure,
  publicProcedure,
} from '~/server/api/trpc';
import { z } from 'zod';
import {
  landingContentSchema,
  updateLandingContentSchema,
  teamMemberSchema,
  updateTeamMemberSchema,
  reorderTeamMembersSchema,
  testimonialSchema,
  updateTestimonialSchema,
  approveTestimonialSchema,
  pricingPlanSchema,
  updatePricingPlanSchema,
  schoolSettingsSchema,
  updateSchoolSettingsSchema,
} from '~/lib/validations/cms';
import { TRPCError } from '@trpc/server';

export const cmsRouter = createTRPCRouter({
  // =========== Landing Page Content ===========

  getPageContent: publicProcedure
    .input(z.object({ section: z.string() }).optional())
    .query(async ({ ctx, input }) => {
      if (input?.section) {
        return await ctx.prisma.landingPageContent.findUnique({
          where: { section: input.section },
        });
      }

      return await ctx.prisma.landingPageContent.findMany({
        where: { isPublished: true },
        orderBy: { section: 'asc' },
      });
    }),

  updatePageContent: adminProcedure
    .input(updateLandingContentSchema)
    .mutation(async ({ ctx, input }) => {
      const { id, ...data } = input;

      return await ctx.prisma.landingPageContent.update({
        where: { id },
        data,
      });
    }),

  createPageContent: adminProcedure
    .input(landingContentSchema)
    .mutation(async ({ ctx, input }) => {
      return await ctx.prisma.landingPageContent.create({
        data: input,
      });
    }),

  // =========== Team Members ===========

  getTeamMembers: publicProcedure.query(async ({ ctx }) => {
    return await ctx.prisma.teamMember.findMany({
      where: { isVisible: true },
      orderBy: { displayOrder: 'asc' },
    });
  }),

  getAllTeamMembers: adminProcedure.query(async ({ ctx }) => {
    return await ctx.prisma.teamMember.findMany({
      orderBy: { displayOrder: 'asc' },
    });
  }),

  createTeamMember: adminProcedure
    .input(teamMemberSchema)
    .mutation(async ({ ctx, input }) => {
      return await ctx.prisma.teamMember.create({
        data: input,
      });
    }),

  updateTeamMember: adminProcedure
    .input(updateTeamMemberSchema)
    .mutation(async ({ ctx, input }) => {
      const { id, ...data } = input;

      return await ctx.prisma.teamMember.update({
        where: { id },
        data,
      });
    }),

  deleteTeamMember: adminProcedure
    .input(z.object({ id: z.string().uuid() }))
    .mutation(async ({ ctx, input }) => {
      return await ctx.prisma.teamMember.delete({
        where: { id: input.id },
      });
    }),

  reorderTeamMembers: adminProcedure
    .input(reorderTeamMembersSchema)
    .mutation(async ({ ctx, input }) => {
      await ctx.prisma.$transaction(
        input.members.map((member) =>
          ctx.prisma.teamMember.update({
            where: { id: member.id },
            data: { displayOrder: member.displayOrder },
          })
        )
      );

      return { success: true };
    }),

  // =========== Testimonials ===========

  getTestimonials: publicProcedure.query(async ({ ctx }) => {
    return await ctx.prisma.testimonial.findMany({
      where: {
        isApproved: true,
        isPublished: true,
      },
      orderBy: { displayOrder: 'asc' },
    });
  }),

  getAllTestimonials: adminProcedure.query(async ({ ctx }) => {
    return await ctx.prisma.testimonial.findMany({
      orderBy: { submittedAt: 'desc' },
    });
  }),

  createTestimonial: adminProcedure
    .input(testimonialSchema)
    .mutation(async ({ ctx, input }) => {
      return await ctx.prisma.testimonial.create({
        data: input,
      });
    }),

  updateTestimonial: adminProcedure
    .input(updateTestimonialSchema)
    .mutation(async ({ ctx, input }) => {
      const { id, ...data } = input;

      return await ctx.prisma.testimonial.update({
        where: { id },
        data,
      });
    }),

  approveTestimonial: adminProcedure
    .input(approveTestimonialSchema)
    .mutation(async ({ ctx, input }) => {
      const { id, isApproved, isPublished } = input;

      return await ctx.prisma.testimonial.update({
        where: { id },
        data: {
          isApproved,
          isPublished: isPublished ?? isApproved,
          approvedAt: isApproved ? new Date() : null,
          approvedBy: isApproved ? ctx.session.user.id : null,
        },
      });
    }),

  deleteTestimonial: adminProcedure
    .input(z.object({ id: z.string().uuid() }))
    .mutation(async ({ ctx, input }) => {
      return await ctx.prisma.testimonial.delete({
        where: { id: input.id },
      });
    }),

  // =========== Pricing Plans ===========

  getPricingPlans: publicProcedure.query(async ({ ctx }) => {
    return await ctx.prisma.pricingPlan.findMany({
      where: { isVisible: true },
      orderBy: { displayOrder: 'asc' },
    });
  }),

  getAllPricingPlans: adminProcedure.query(async ({ ctx }) => {
    return await ctx.prisma.pricingPlan.findMany({
      orderBy: { displayOrder: 'asc' },
    });
  }),

  createPricingPlan: adminProcedure
    .input(pricingPlanSchema)
    .mutation(async ({ ctx, input }) => {
      return await ctx.prisma.pricingPlan.create({
        data: input,
      });
    }),

  updatePricingPlan: adminProcedure
    .input(updatePricingPlanSchema)
    .mutation(async ({ ctx, input }) => {
      const { id, ...data } = input;

      return await ctx.prisma.pricingPlan.update({
        where: { id },
        data,
      });
    }),

  deletePricingPlan: adminProcedure
    .input(z.object({ id: z.string().uuid() }))
    .mutation(async ({ ctx, input }) => {
      return await ctx.prisma.pricingPlan.delete({
        where: { id: input.id },
      });
    }),

  // =========== School Settings ===========

  getSchoolSettings: publicProcedure.query(async ({ ctx }) => {
    const settings = await ctx.prisma.schoolSettings.findFirst();

    if (!settings) {
      // Create default settings if none exist
      return await ctx.prisma.schoolSettings.create({
        data: {
          schoolName: 'Na Piątkę',
          country: 'Polska',
        },
      });
    }

    return settings;
  }),

  updateSchoolSettings: adminProcedure
    .input(updateSchoolSettingsSchema)
    .mutation(async ({ ctx, input }) => {
      const { id, ...data } = input;

      return await ctx.prisma.schoolSettings.update({
        where: { id },
        data: {
          ...data,
          updatedBy: ctx.session.user.id,
        },
      });
    }),
});
```

**Validation**:

- All endpoints properly typed
- Admin-only mutations protected
- Public queries for landing page
- Proper error handling
- Input validation with Zod

---

### Task 044I: Content Editor (Rich Text)

**Files**:

- `components/features/cms/RichTextEditor.tsx`
- `components/features/cms/ContentEditor.tsx`
- `lib/tiptap-extensions.ts`
- `package.json` (add Tiptap dependencies)

#### Install Tiptap Dependencies:

```bash
pnpm add @tiptap/react@^2.1.0 @tiptap/starter-kit@^2.1.0
pnpm add @tiptap/extension-link@^2.1.0 @tiptap/extension-image@^2.1.0
pnpm add @tiptap/extension-color@^2.1.0 @tiptap/extension-text-style@^2.1.0
pnpm add @tiptap/extension-heading@^2.1.0 @tiptap/extension-bullet-list@^2.1.0
```

#### Rich Text Editor Component:

```typescript
// components/features/cms/RichTextEditor.tsx
'use client';

import { useEditor, EditorContent, type Editor } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Link from '@tiptap/extension-link';
import Image from '@tiptap/extension-image';
import Color from '@tiptap/extension-color';
import TextStyle from '@tiptap/extension-text-style';
import Heading from '@tiptap/extension-heading';
import { useCallback } from 'react';
import { Button } from '~/components/ui/button';
import { Separator } from '~/components/ui/separator';
import {
  Bold,
  Italic,
  Strikethrough,
  Code,
  Heading1,
  Heading2,
  Heading3,
  List,
  ListOrdered,
  Quote,
  Undo,
  Redo,
  Link as LinkIcon,
  Image as ImageIcon,
  Palette,
} from 'lucide-react';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '~/components/ui/popover';
import { Input } from '~/components/ui/input';
import { useState } from 'react';

interface RichTextEditorProps {
  content: string;
  onChange: (content: string) => void;
  placeholder?: string;
  editable?: boolean;
  minHeight?: string;
}

export function RichTextEditor({
  content,
  onChange,
  placeholder = 'Zacznij pisać...',
  editable = true,
  minHeight = '200px',
}: RichTextEditorProps) {
  const editor = useEditor({
    extensions: [
      StarterKit,
      Link.configure({
        openOnClick: false,
        HTMLAttributes: {
          class: 'text-blue-500 underline',
        },
      }),
      Image.configure({
        HTMLAttributes: {
          class: 'max-w-full h-auto rounded-lg',
        },
      }),
      Color,
      TextStyle,
      Heading.configure({
        levels: [1, 2, 3],
      }),
    ],
    content,
    editable,
    onUpdate: ({ editor }) => {
      onChange(editor.getHTML());
    },
    editorProps: {
      attributes: {
        class: 'prose prose-sm max-w-none focus:outline-none p-4',
        style: `min-height: ${minHeight}`,
      },
    },
  });

  if (!editor) {
    return null;
  }

  return (
    <div className="border rounded-lg bg-white">
      <MenuBar editor={editor} />
      <Separator />
      <EditorContent editor={editor} />
    </div>
  );
}

interface MenuBarProps {
  editor: Editor;
}

function MenuBar({ editor }: MenuBarProps) {
  const [linkUrl, setLinkUrl] = useState('');
  const [imageUrl, setImageUrl] = useState('');
  const [isLinkOpen, setIsLinkOpen] = useState(false);
  const [isImageOpen, setIsImageOpen] = useState(false);

  const setLink = useCallback(() => {
    if (linkUrl) {
      editor
        .chain()
        .focus()
        .extendMarkRange('link')
        .setLink({ href: linkUrl })
        .run();
    }
    setLinkUrl('');
    setIsLinkOpen(false);
  }, [editor, linkUrl]);

  const addImage = useCallback(() => {
    if (imageUrl) {
      editor.chain().focus().setImage({ src: imageUrl }).run();
    }
    setImageUrl('');
    setIsImageOpen(false);
  }, [editor, imageUrl]);

  const setColor = useCallback(
    (color: string) => {
      editor.chain().focus().setColor(color).run();
    },
    [editor]
  );

  return (
    <div className="flex flex-wrap items-center gap-1 p-2 border-b">
      {/* Text Formatting */}
      <Button
        variant={editor.isActive('bold') ? 'default' : 'ghost'}
        size="sm"
        onClick={() => editor.chain().focus().toggleBold().run()}
        title="Pogrubienie (Ctrl+B)"
      >
        <Bold className="h-4 w-4" />
      </Button>

      <Button
        variant={editor.isActive('italic') ? 'default' : 'ghost'}
        size="sm"
        onClick={() => editor.chain().focus().toggleItalic().run()}
        title="Kursywa (Ctrl+I)"
      >
        <Italic className="h-4 w-4" />
      </Button>

      <Button
        variant={editor.isActive('strike') ? 'default' : 'ghost'}
        size="sm"
        onClick={() => editor.chain().focus().toggleStrike().run()}
        title="Przekreślenie"
      >
        <Strikethrough className="h-4 w-4" />
      </Button>

      <Button
        variant={editor.isActive('code') ? 'default' : 'ghost'}
        size="sm"
        onClick={() => editor.chain().focus().toggleCode().run()}
        title="Kod"
      >
        <Code className="h-4 w-4" />
      </Button>

      <Separator orientation="vertical" className="h-6 mx-1" />

      {/* Headings */}
      <Button
        variant={editor.isActive('heading', { level: 1 }) ? 'default' : 'ghost'}
        size="sm"
        onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
        title="Nagłówek 1"
      >
        <Heading1 className="h-4 w-4" />
      </Button>

      <Button
        variant={editor.isActive('heading', { level: 2 }) ? 'default' : 'ghost'}
        size="sm"
        onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
        title="Nagłówek 2"
      >
        <Heading2 className="h-4 w-4" />
      </Button>

      <Button
        variant={editor.isActive('heading', { level: 3 }) ? 'default' : 'ghost'}
        size="sm"
        onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
        title="Nagłówek 3"
      >
        <Heading3 className="h-4 w-4" />
      </Button>

      <Separator orientation="vertical" className="h-6 mx-1" />

      {/* Lists */}
      <Button
        variant={editor.isActive('bulletList') ? 'default' : 'ghost'}
        size="sm"
        onClick={() => editor.chain().focus().toggleBulletList().run()}
        title="Lista punktowana"
      >
        <List className="h-4 w-4" />
      </Button>

      <Button
        variant={editor.isActive('orderedList') ? 'default' : 'ghost'}
        size="sm"
        onClick={() => editor.chain().focus().toggleOrderedList().run()}
        title="Lista numerowana"
      >
        <ListOrdered className="h-4 w-4" />
      </Button>

      <Button
        variant={editor.isActive('blockquote') ? 'default' : 'ghost'}
        size="sm"
        onClick={() => editor.chain().focus().toggleBlockquote().run()}
        title="Cytat"
      >
        <Quote className="h-4 w-4" />
      </Button>

      <Separator orientation="vertical" className="h-6 mx-1" />

      {/* Link */}
      <Popover open={isLinkOpen} onOpenChange={setIsLinkOpen}>
        <PopoverTrigger asChild>
          <Button
            variant={editor.isActive('link') ? 'default' : 'ghost'}
            size="sm"
            title="Dodaj link"
          >
            <LinkIcon className="h-4 w-4" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-80">
          <div className="space-y-2">
            <h4 className="font-medium text-sm">Dodaj link</h4>
            <Input
              placeholder="https://example.com"
              value={linkUrl}
              onChange={(e) => setLinkUrl(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  setLink();
                }
              }}
            />
            <div className="flex justify-end space-x-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  editor.chain().focus().unsetLink().run();
                  setIsLinkOpen(false);
                }}
              >
                Usuń
              </Button>
              <Button size="sm" onClick={setLink}>
                Dodaj
              </Button>
            </div>
          </div>
        </PopoverContent>
      </Popover>

      {/* Image */}
      <Popover open={isImageOpen} onOpenChange={setIsImageOpen}>
        <PopoverTrigger asChild>
          <Button variant="ghost" size="sm" title="Dodaj obraz">
            <ImageIcon className="h-4 w-4" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-80">
          <div className="space-y-2">
            <h4 className="font-medium text-sm">Dodaj obraz</h4>
            <Input
              placeholder="https://example.com/image.jpg"
              value={imageUrl}
              onChange={(e) => setImageUrl(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  addImage();
                }
              }}
            />
            <Button size="sm" onClick={addImage} className="w-full">
              Dodaj obraz
            </Button>
          </div>
        </PopoverContent>
      </Popover>

      {/* Color Picker */}
      <Popover>
        <PopoverTrigger asChild>
          <Button variant="ghost" size="sm" title="Kolor tekstu">
            <Palette className="h-4 w-4" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-64">
          <div className="grid grid-cols-6 gap-2">
            {[
              '#000000',
              '#EF4444',
              '#F59E0B',
              '#10B981',
              '#3B82F6',
              '#8B5CF6',
              '#EC4899',
              '#6B7280',
            ].map((color) => (
              <button
                key={color}
                className="w-8 h-8 rounded border-2 border-gray-200 hover:border-gray-400"
                style={{ backgroundColor: color }}
                onClick={() => setColor(color)}
              />
            ))}
          </div>
        </PopoverContent>
      </Popover>

      <Separator orientation="vertical" className="h-6 mx-1" />

      {/* Undo/Redo */}
      <Button
        variant="ghost"
        size="sm"
        onClick={() => editor.chain().focus().undo().run()}
        disabled={!editor.can().undo()}
        title="Cofnij (Ctrl+Z)"
      >
        <Undo className="h-4 w-4" />
      </Button>

      <Button
        variant="ghost"
        size="sm"
        onClick={() => editor.chain().focus().redo().run()}
        disabled={!editor.can().redo()}
        title="Ponów (Ctrl+Shift+Z)"
      >
        <Redo className="h-4 w-4" />
      </Button>
    </div>
  );
}
```

#### Content Editor Form:

```typescript
// components/features/cms/ContentEditor.tsx
'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
  FormDescription,
} from '~/components/ui/form';
import { Input } from '~/components/ui/input';
import { Button } from '~/components/ui/button';
import { Switch } from '~/components/ui/switch';
import { RichTextEditor } from './RichTextEditor';
import { updateLandingContentSchema, type LandingContentInput } from '~/lib/validations/cms';
import { api } from '~/utils/api';
import { useToast } from '~/hooks/use-toast';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '~/components/ui/card';
import { Save, Eye, EyeOff } from 'lucide-react';

interface ContentEditorProps {
  section: 'hero' | 'about' | 'features' | 'cta';
  title: string;
  description: string;
}

export function ContentEditor({ section, title, description }: ContentEditorProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();
  const utils = api.useUtils();

  // Fetch current content
  const { data: content, isLoading } = api.cms.getPageContent.useQuery({ section });

  const form = useForm({
    resolver: zodResolver(updateLandingContentSchema),
    values: content || {
      section,
      title: '',
      subtitle: '',
      content: null,
      imageUrl: '',
      buttonText: '',
      buttonUrl: '',
      isPublished: true,
    },
  });

  const onSubmit = async (data: any) => {
    setIsSubmitting(true);

    try {
      if (content?.id) {
        await api.cms.updatePageContent.mutate({ id: content.id, ...data });
        toast({ title: 'Zawartość została zaktualizowana' });
      } else {
        await api.cms.createPageContent.mutate(data);
        toast({ title: 'Zawartość została utworzona' });
      }

      utils.cms.getPageContent.invalidate();
    } catch (error: any) {
      toast({
        title: 'Błąd',
        description: error.message,
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return <div className="animate-pulse h-96 bg-gray-100 rounded-lg" />;
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>{title}</CardTitle>
            <CardDescription>{description}</CardDescription>
          </div>
          <div className="flex items-center space-x-2">
            <FormField
              control={form.control}
              name="isPublished"
              render={({ field }) => (
                <FormItem className="flex items-center space-x-2">
                  <FormControl>
                    <Switch checked={field.value} onCheckedChange={field.onChange} />
                  </FormControl>
                  <FormLabel className="!mt-0">
                    {field.value ? (
                      <span className="flex items-center space-x-1 text-green-600">
                        <Eye className="h-4 w-4" />
                        <span>Opublikowane</span>
                      </span>
                    ) : (
                      <span className="flex items-center space-x-1 text-gray-600">
                        <EyeOff className="h-4 w-4" />
                        <span>Ukryte</span>
                      </span>
                    )}
                  </FormLabel>
                </FormItem>
              )}
            />
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="title"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Tytuł</FormLabel>
                    <FormControl>
                      <Input {...field} placeholder="Tytuł sekcji..." />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="subtitle"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Podtytuł</FormLabel>
                    <FormControl>
                      <Input {...field} placeholder="Podtytuł sekcji..." />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="content"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Treść</FormLabel>
                  <FormControl>
                    <RichTextEditor
                      content={field.value ? JSON.stringify(field.value) : ''}
                      onChange={(html) => field.onChange(html)}
                      minHeight="300px"
                    />
                  </FormControl>
                  <FormDescription>
                    Użyj paska narzędzi aby sformatować tekst, dodać linki i obrazy
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="imageUrl"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>URL obrazu</FormLabel>
                    <FormControl>
                      <Input {...field} placeholder="https://..." />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="buttonText"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Tekst przycisku</FormLabel>
                    <FormControl>
                      <Input {...field} placeholder="np. Dowiedz się więcej" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="buttonUrl"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>URL przycisku</FormLabel>
                  <FormControl>
                    <Input {...field} placeholder="/kontakt" />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="flex justify-end">
              <Button type="submit" disabled={isSubmitting}>
                <Save className="h-4 w-4 mr-2" />
                {isSubmitting ? 'Zapisywanie...' : 'Zapisz zmiany'}
              </Button>
            </div>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
```

**Validation**:

- Rich text editor fully functional
- All formatting tools working
- Content saves to database
- Preview mode available
- Responsive design

---

### Task 044J: Team Members Management

**Files**:

- `components/features/cms/TeamMembersManager.tsx`
- `components/features/cms/TeamMemberForm.tsx`
- `components/features/cms/TeamMemberCard.tsx`

#### Team Members Manager with Drag & Drop:

```bash
# Install drag & drop library
pnpm add @dnd-kit/core@^6.1.0 @dnd-kit/sortable@^8.0.0 @dnd-kit/utilities@^3.2.2
```

```typescript
// components/features/cms/TeamMembersManager.tsx
'use client';

import { useState } from 'react';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { api } from '~/utils/api';
import { Button } from '~/components/ui/button';
import { Plus } from 'lucide-react';
import { TeamMemberCard } from './TeamMemberCard';
import { TeamMemberForm } from './TeamMemberForm';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '~/components/ui/dialog';
import { useToast } from '~/hooks/use-toast';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '~/components/ui/card';

export function TeamMembersManager() {
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingMember, setEditingMember] = useState<any>(null);
  const { toast } = useToast();
  const utils = api.useUtils();

  const { data: members, isLoading } = api.cms.getAllTeamMembers.useQuery();

  const reorderMutation = api.cms.reorderTeamMembers.useMutation({
    onSuccess: () => {
      utils.cms.getAllTeamMembers.invalidate();
      toast({ title: 'Kolejność zaktualizowana' });
    },
  });

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      const oldIndex = members?.findIndex((m) => m.id === active.id) ?? -1;
      const newIndex = members?.findIndex((m) => m.id === over.id) ?? -1;

      if (oldIndex !== -1 && newIndex !== -1 && members) {
        const newOrder = arrayMove(members, oldIndex, newIndex);

        // Update display order
        const reorderedMembers = newOrder.map((member, index) => ({
          id: member.id,
          displayOrder: index,
        }));

        reorderMutation.mutate({ members: reorderedMembers });
      }
    }
  };

  const handleEdit = (member: any) => {
    setEditingMember(member);
    setIsFormOpen(true);
  };

  const handleCloseForm = () => {
    setIsFormOpen(false);
    setEditingMember(null);
  };

  if (isLoading) {
    return <div className="animate-pulse h-96 bg-gray-100 rounded-lg" />;
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Zarządzanie zespołem</CardTitle>
            <CardDescription>
              Przeciągnij i upuść aby zmienić kolejność wyświetlania
            </CardDescription>
          </div>
          <Button onClick={() => setIsFormOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Dodaj członka zespołu
          </Button>
        </div>
      </CardHeader>

      <CardContent>
        <DndContext
          sensors={sensors}
          collisionDetection={closestCenter}
          onDragEnd={handleDragEnd}
        >
          <SortableContext
            items={members?.map((m) => m.id) ?? []}
            strategy={verticalListSortingStrategy}
          >
            <div className="space-y-4">
              {members?.map((member) => (
                <TeamMemberCard
                  key={member.id}
                  member={member}
                  onEdit={() => handleEdit(member)}
                />
              ))}
            </div>
          </SortableContext>
        </DndContext>

        {(!members || members.length === 0) && (
          <div className="text-center py-12 text-gray-500">
            Brak członków zespołu. Dodaj pierwszego klikając przycisk powyżej.
          </div>
        )}
      </CardContent>

      <Dialog open={isFormOpen} onOpenChange={setIsFormOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {editingMember ? 'Edytuj członka zespołu' : 'Dodaj członka zespołu'}
            </DialogTitle>
          </DialogHeader>
          <TeamMemberForm member={editingMember} onClose={handleCloseForm} />
        </DialogContent>
      </Dialog>
    </Card>
  );
}
```

#### Team Member Card (Sortable):

```typescript
// components/features/cms/TeamMemberCard.tsx
'use client';

import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { Card, CardContent } from '~/components/ui/card';
import { Button } from '~/components/ui/button';
import { Badge } from '~/components/ui/badge';
import { GripVertical, Edit, Trash2, Eye, EyeOff, Mail, Phone, Linkedin } from 'lucide-react';
import { Avatar, AvatarImage, AvatarFallback } from '~/components/ui/avatar';
import { api } from '~/utils/api';
import { useToast } from '~/hooks/use-toast';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '~/components/ui/alert-dialog';

interface TeamMemberCardProps {
  member: any;
  onEdit: () => void;
}

export function TeamMemberCard({ member, onEdit }: TeamMemberCardProps) {
  const { toast } = useToast();
  const utils = api.useUtils();

  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: member.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const deleteMutation = api.cms.deleteTeamMember.useMutation({
    onSuccess: () => {
      utils.cms.getAllTeamMembers.invalidate();
      toast({ title: 'Członek zespołu został usunięty' });
    },
    onError: (error) => {
      toast({
        title: 'Błąd',
        description: error.message,
        variant: 'destructive',
      });
    },
  });

  const updateMutation = api.cms.updateTeamMember.useMutation({
    onSuccess: () => {
      utils.cms.getAllTeamMembers.invalidate();
      toast({ title: 'Widoczność zaktualizowana' });
    },
  });

  const toggleVisibility = () => {
    updateMutation.mutate({
      id: member.id,
      isVisible: !member.isVisible,
    });
  };

  return (
    <Card ref={setNodeRef} style={style}>
      <CardContent className="p-4">
        <div className="flex items-center space-x-4">
          {/* Drag Handle */}
          <button
            className="cursor-grab active:cursor-grabbing text-gray-400 hover:text-gray-600"
            {...attributes}
            {...listeners}
          >
            <GripVertical className="h-5 w-5" />
          </button>

          {/* Avatar */}
          <Avatar className="h-16 w-16">
            <AvatarImage src={member.imageUrl} alt={`${member.name} ${member.surname}`} />
            <AvatarFallback>
              {member.name[0]}
              {member.surname[0]}
            </AvatarFallback>
          </Avatar>

          {/* Info */}
          <div className="flex-1">
            <div className="flex items-center space-x-2">
              <h3 className="font-semibold">
                {member.name} {member.surname}
              </h3>
              <Badge variant={member.isVisible ? 'default' : 'secondary'}>
                {member.isVisible ? 'Widoczny' : 'Ukryty'}
              </Badge>
            </div>
            <p className="text-sm text-gray-600">{member.position}</p>
            {member.bio && (
              <p className="text-sm text-gray-500 mt-1 line-clamp-2">{member.bio}</p>
            )}
            <div className="flex items-center space-x-3 mt-2 text-xs text-gray-500">
              {member.email && (
                <span className="flex items-center space-x-1">
                  <Mail className="h-3 w-3" />
                  <span>{member.email}</span>
                </span>
              )}
              {member.phone && (
                <span className="flex items-center space-x-1">
                  <Phone className="h-3 w-3" />
                  <span>{member.phone}</span>
                </span>
              )}
              {member.linkedIn && (
                <span className="flex items-center space-x-1">
                  <Linkedin className="h-3 w-3" />
                  <span>LinkedIn</span>
                </span>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center space-x-2">
            <Button variant="ghost" size="sm" onClick={toggleVisibility}>
              {member.isVisible ? (
                <Eye className="h-4 w-4" />
              ) : (
                <EyeOff className="h-4 w-4" />
              )}
            </Button>

            <Button variant="ghost" size="sm" onClick={onEdit}>
              <Edit className="h-4 w-4" />
            </Button>

            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button variant="ghost" size="sm" className="text-red-600 hover:text-red-700">
                  <Trash2 className="h-4 w-4" />
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Czy na pewno chcesz usunąć?</AlertDialogTitle>
                  <AlertDialogDescription>
                    Ta akcja jest nieodwracalna. Członek zespołu zostanie trwale usunięty.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Anuluj</AlertDialogCancel>
                  <AlertDialogAction
                    onClick={() => deleteMutation.mutate({ id: member.id })}
                    className="bg-red-600 hover:bg-red-700"
                  >
                    Usuń
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
```

#### Team Member Form:

```typescript
// components/features/cms/TeamMemberForm.tsx
'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '~/components/ui/form';
import { Input } from '~/components/ui/input';
import { Textarea } from '~/components/ui/textarea';
import { Button } from '~/components/ui/button';
import { Switch } from '~/components/ui/switch';
import { teamMemberSchema, type TeamMemberInput } from '~/lib/validations/cms';
import { api } from '~/utils/api';
import { useToast } from '~/hooks/use-toast';
import { Save } from 'lucide-react';

interface TeamMemberFormProps {
  member?: any;
  onClose: () => void;
}

export function TeamMemberForm({ member, onClose }: TeamMemberFormProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();
  const utils = api.useUtils();

  const form = useForm<TeamMemberInput>({
    resolver: zodResolver(teamMemberSchema),
    defaultValues: member || {
      name: '',
      surname: '',
      position: '',
      bio: '',
      imageUrl: '',
      linkedIn: '',
      email: '',
      phone: '',
      displayOrder: 0,
      isVisible: true,
    },
  });

  const createMutation = api.cms.createTeamMember.useMutation();
  const updateMutation = api.cms.updateTeamMember.useMutation();

  const onSubmit = async (data: TeamMemberInput) => {
    setIsSubmitting(true);

    try {
      if (member) {
        await updateMutation.mutateAsync({ id: member.id, ...data });
        toast({ title: 'Członek zespołu zaktualizowany' });
      } else {
        await createMutation.mutateAsync(data);
        toast({ title: 'Członek zespołu dodany' });
      }

      utils.cms.getAllTeamMembers.invalidate();
      onClose();
    } catch (error: any) {
      toast({
        title: 'Błąd',
        description: error.message,
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <FormField
            control={form.control}
            name="name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Imię *</FormLabel>
                <FormControl>
                  <Input {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="surname"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Nazwisko *</FormLabel>
                <FormControl>
                  <Input {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <FormField
          control={form.control}
          name="position"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Stanowisko *</FormLabel>
              <FormControl>
                <Input {...field} placeholder="np. Korepetytor matematyki" />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="bio"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Bio</FormLabel>
              <FormControl>
                <Textarea {...field} rows={4} placeholder="Krótki opis..." />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="imageUrl"
          render={({ field }) => (
            <FormItem>
              <FormLabel>URL zdjęcia</FormLabel>
              <FormControl>
                <Input {...field} placeholder="https://..." />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="grid grid-cols-2 gap-4">
          <FormField
            control={form.control}
            name="email"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Email</FormLabel>
                <FormControl>
                  <Input {...field} type="email" />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="phone"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Telefon</FormLabel>
                <FormControl>
                  <Input {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <FormField
          control={form.control}
          name="linkedIn"
          render={({ field }) => (
            <FormItem>
              <FormLabel>LinkedIn</FormLabel>
              <FormControl>
                <Input {...field} placeholder="https://linkedin.com/in/..." />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="isVisible"
          render={({ field }) => (
            <FormItem className="flex items-center justify-between">
              <FormLabel>Widoczny na stronie</FormLabel>
              <FormControl>
                <Switch checked={field.value} onCheckedChange={field.onChange} />
              </FormControl>
            </FormItem>
          )}
        />

        <div className="flex justify-end space-x-2">
          <Button type="button" variant="outline" onClick={onClose}>
            Anuluj
          </Button>
          <Button type="submit" disabled={isSubmitting}>
            <Save className="h-4 w-4 mr-2" />
            {isSubmitting ? 'Zapisywanie...' : 'Zapisz'}
          </Button>
        </div>
      </form>
    </Form>
  );
}
```

**Validation**:

- Drag & drop reordering works
- CRUD operations functional
- Visibility toggle works
- Form validation correct
- Responsive cards

---

### Task 044K: Testimonials Moderation

**Files**:

- `components/features/cms/TestimonialsModeration.tsx`
- `components/features/cms/TestimonialCard.tsx`

#### Testimonials Moderation Component:

```typescript
// components/features/cms/TestimonialsModeration.tsx
'use client';

import { useState } from 'react';
import { api } from '~/utils/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '~/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '~/components/ui/tabs';
import { Button } from '~/components/ui/button';
import { Badge } from '~/components/ui/badge';
import { useToast } from '~/hooks/use-toast';
import { Avatar, AvatarFallback, AvatarImage } from '~/components/ui/avatar';
import { CheckCircle2, XCircle, Star, Eye, EyeOff, Trash2 } from 'lucide-react';
import { format } from 'date-fns';
import { pl } from 'date-fns/locale';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '~/components/ui/alert-dialog';

export function TestimonialsModeration() {
  const [activeTab, setActiveTab] = useState('pending');
  const { toast } = useToast();
  const utils = api.useUtils();

  const { data: allTestimonials, isLoading } = api.cms.getAllTestimonials.useQuery();

  const approveMutation = api.cms.approveTestimonial.useMutation({
    onSuccess: () => {
      utils.cms.getAllTestimonials.invalidate();
      toast({ title: 'Status opinii zaktualizowany' });
    },
  });

  const deleteMutation = api.cms.deleteTestimonial.useMutation({
    onSuccess: () => {
      utils.cms.getAllTestimonials.invalidate();
      toast({ title: 'Opinia została usunięta' });
    },
  });

  const pendingTestimonials = allTestimonials?.filter((t) => !t.isApproved) || [];
  const approvedTestimonials = allTestimonials?.filter((t) => t.isApproved) || [];

  const handleApprove = (id: string, publish: boolean = true) => {
    approveMutation.mutate({
      id,
      isApproved: true,
      isPublished: publish,
    });
  };

  const handleReject = (id: string) => {
    deleteMutation.mutate({ id });
  };

  const handleTogglePublish = (testimonial: any) => {
    approveMutation.mutate({
      id: testimonial.id,
      isApproved: true,
      isPublished: !testimonial.isPublished,
    });
  };

  if (isLoading) {
    return <div className="animate-pulse h-96 bg-gray-100 rounded-lg" />;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Moderacja opinii</CardTitle>
        <CardDescription>
          Przeglądaj i zatwierdzaj opinie klientów przed publikacją
        </CardDescription>
      </CardHeader>

      <CardContent>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="pending">
              Oczekujące ({pendingTestimonials.length})
            </TabsTrigger>
            <TabsTrigger value="approved">
              Zatwierdzone ({approvedTestimonials.length})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="pending" className="space-y-4 mt-4">
            {pendingTestimonials.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                Brak opinii oczekujących na moderację
              </div>
            ) : (
              pendingTestimonials.map((testimonial) => (
                <TestimonialModerationCard
                  key={testimonial.id}
                  testimonial={testimonial}
                  onApprove={(publish) => handleApprove(testimonial.id, publish)}
                  onReject={() => handleReject(testimonial.id)}
                />
              ))
            )}
          </TabsContent>

          <TabsContent value="approved" className="space-y-4 mt-4">
            {approvedTestimonials.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                Brak zatwierdzonych opinii
              </div>
            ) : (
              approvedTestimonials.map((testimonial) => (
                <TestimonialApprovedCard
                  key={testimonial.id}
                  testimonial={testimonial}
                  onTogglePublish={() => handleTogglePublish(testimonial)}
                  onDelete={() => handleReject(testimonial.id)}
                />
              ))
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}

interface TestimonialModerationCardProps {
  testimonial: any;
  onApprove: (publish: boolean) => void;
  onReject: () => void;
}

function TestimonialModerationCard({
  testimonial,
  onApprove,
  onReject,
}: TestimonialModerationCardProps) {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-start space-x-4">
          <Avatar className="h-12 w-12">
            <AvatarImage src={testimonial.imageUrl} />
            <AvatarFallback>{testimonial.authorName[0]}</AvatarFallback>
          </Avatar>

          <div className="flex-1">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-semibold">{testimonial.authorName}</h4>
                <div className="flex items-center space-x-2 text-sm text-gray-600">
                  {testimonial.authorRole && (
                    <Badge variant="secondary">{testimonial.authorRole}</Badge>
                  )}
                  <span>
                    {format(new Date(testimonial.submittedAt), 'dd MMM yyyy', { locale: pl })}
                  </span>
                </div>
              </div>

              <div className="flex items-center">
                {[...Array(5)].map((_, i) => (
                  <Star
                    key={i}
                    className={`h-4 w-4 ${
                      i < testimonial.rating
                        ? 'text-yellow-400 fill-yellow-400'
                        : 'text-gray-300'
                    }`}
                  />
                ))}
              </div>
            </div>

            <p className="mt-3 text-gray-700">{testimonial.content}</p>

            <div className="flex items-center space-x-2 mt-4">
              <Button size="sm" onClick={() => onApprove(true)}>
                <CheckCircle2 className="h-4 w-4 mr-2" />
                Zatwierdź i opublikuj
              </Button>

              <Button size="sm" variant="outline" onClick={() => onApprove(false)}>
                <CheckCircle2 className="h-4 w-4 mr-2" />
                Zatwierdź bez publikacji
              </Button>

              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button size="sm" variant="destructive">
                    <XCircle className="h-4 w-4 mr-2" />
                    Odrzuć
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Odrzucić opinię?</AlertDialogTitle>
                    <AlertDialogDescription>
                      Ta opinia zostanie trwale usunięta z systemu.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Anuluj</AlertDialogCancel>
                    <AlertDialogAction onClick={onReject}>Odrzuć</AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

interface TestimonialApprovedCardProps {
  testimonial: any;
  onTogglePublish: () => void;
  onDelete: () => void;
}

function TestimonialApprovedCard({
  testimonial,
  onTogglePublish,
  onDelete,
}: TestimonialApprovedCardProps) {
  return (
    <Card className={testimonial.isPublished ? 'border-green-200' : 'border-gray-200'}>
      <CardContent className="p-6">
        <div className="flex items-start space-x-4">
          <Avatar className="h-12 w-12">
            <AvatarImage src={testimonial.imageUrl} />
            <AvatarFallback>{testimonial.authorName[0]}</AvatarFallback>
          </Avatar>

          <div className="flex-1">
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center space-x-2">
                  <h4 className="font-semibold">{testimonial.authorName}</h4>
                  <Badge variant={testimonial.isPublished ? 'default' : 'secondary'}>
                    {testimonial.isPublished ? 'Opublikowane' : 'Ukryte'}
                  </Badge>
                </div>
                <div className="flex items-center space-x-2 text-sm text-gray-600 mt-1">
                  {testimonial.authorRole && (
                    <Badge variant="outline">{testimonial.authorRole}</Badge>
                  )}
                  <span>
                    Zatwierdzone:{' '}
                    {format(new Date(testimonial.approvedAt), 'dd MMM yyyy', { locale: pl })}
                  </span>
                </div>
              </div>

              <div className="flex items-center">
                {[...Array(5)].map((_, i) => (
                  <Star
                    key={i}
                    className={`h-4 w-4 ${
                      i < testimonial.rating
                        ? 'text-yellow-400 fill-yellow-400'
                        : 'text-gray-300'
                    }`}
                  />
                ))}
              </div>
            </div>

            <p className="mt-3 text-gray-700">{testimonial.content}</p>

            <div className="flex items-center space-x-2 mt-4">
              <Button size="sm" variant="outline" onClick={onTogglePublish}>
                {testimonial.isPublished ? (
                  <>
                    <EyeOff className="h-4 w-4 mr-2" />
                    Ukryj
                  </>
                ) : (
                  <>
                    <Eye className="h-4 w-4 mr-2" />
                    Opublikuj
                  </>
                )}
              </Button>

              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button size="sm" variant="ghost" className="text-red-600">
                    <Trash2 className="h-4 w-4 mr-2" />
                    Usuń
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Usunąć opinię?</AlertDialogTitle>
                    <AlertDialogDescription>
                      Ta akcja jest nieodwracalna. Opinia zostanie trwale usunięta.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Anuluj</AlertDialogCancel>
                    <AlertDialogAction onClick={onDelete} className="bg-red-600">
                      Usuń
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
```

**Validation**:

- Moderation workflow functional
- Approve/reject working
- Publish/unpublish toggle works
- Rating display correct
- Delete confirmation working

---

### Task 044L: Pricing Editor

**Files**:

- `components/features/cms/PricingEditor.tsx`
- `components/features/cms/PricingPlanCard.tsx`

#### Pricing Editor Component:

```typescript
// components/features/cms/PricingEditor.tsx
'use client';

import { useState } from 'react';
import { api } from '~/utils/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '~/components/ui/card';
import { Button } from '~/components/ui/button';
import { Plus } from 'lucide-react';
import { PricingPlanCard } from './PricingPlanCard';
import { PricingPlanForm } from './PricingPlanForm';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '~/components/ui/dialog';

export function PricingEditor() {
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingPlan, setEditingPlan] = useState<any>(null);

  const { data: plans, isLoading } = api.cms.getAllPricingPlans.useQuery();

  const handleEdit = (plan: any) => {
    setEditingPlan(plan);
    setIsFormOpen(true);
  };

  const handleCloseForm = () => {
    setIsFormOpen(false);
    setEditingPlan(null);
  };

  if (isLoading) {
    return <div className="animate-pulse h-96 bg-gray-100 rounded-lg" />;
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Plany cenowe</CardTitle>
            <CardDescription>
              Zarządzaj cenami i pakietami korepetycji
            </CardDescription>
          </div>
          <Button onClick={() => setIsFormOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Dodaj plan
          </Button>
        </div>
      </CardHeader>

      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {plans?.map((plan) => (
            <PricingPlanCard
              key={plan.id}
              plan={plan}
              onEdit={() => handleEdit(plan)}
            />
          ))}
        </div>

        {(!plans || plans.length === 0) && (
          <div className="text-center py-12 text-gray-500">
            Brak planów cenowych. Dodaj pierwszy plan klikając przycisk powyżej.
          </div>
        )}
      </CardContent>

      <Dialog open={isFormOpen} onOpenChange={setIsFormOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {editingPlan ? 'Edytuj plan cenowy' : 'Dodaj plan cenowy'}
            </DialogTitle>
          </DialogHeader>
          <PricingPlanForm plan={editingPlan} onClose={handleCloseForm} />
        </DialogContent>
      </Dialog>
    </Card>
  );
}

// components/features/cms/PricingPlanCard.tsx
interface PricingPlanCardProps {
  plan: any;
  onEdit: () => void;
}

export function PricingPlanCard({ plan, onEdit }: PricingPlanCardProps) {
  const { toast } = useToast();
  const utils = api.useUtils();

  const deleteMutation = api.cms.deletePricingPlan.useMutation({
    onSuccess: () => {
      utils.cms.getAllPricingPlans.invalidate();
      toast({ title: 'Plan został usunięty' });
    },
  });

  return (
    <Card className={plan.isPopular ? 'border-blue-500 border-2' : ''}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-xl">{plan.name}</CardTitle>
          {plan.isPopular && <Badge>Najpopularniejszy</Badge>}
        </div>
        {plan.description && (
          <CardDescription>{plan.description}</CardDescription>
        )}
      </CardHeader>

      <CardContent>
        <div className="text-3xl font-bold mb-4">
          {plan.price} {plan.priceUnit}
        </div>

        <ul className="space-y-2 mb-6">
          {JSON.parse(plan.features).map((feature: string, index: number) => (
            <li key={index} className="flex items-start space-x-2">
              <CheckCircle2 className="h-5 w-5 text-green-500 mt-0.5" />
              <span className="text-sm">{feature}</span>
            </li>
          ))}
        </ul>

        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm" onClick={onEdit} className="flex-1">
            <Edit className="h-4 w-4 mr-2" />
            Edytuj
          </Button>

          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="ghost" size="sm" className="text-red-600">
                <Trash2 className="h-4 w-4" />
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Usunąć plan?</AlertDialogTitle>
                <AlertDialogDescription>
                  Ta akcja jest nieodwracalna.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Anuluj</AlertDialogCancel>
                <AlertDialogAction
                  onClick={() => deleteMutation.mutate({ id: plan.id })}
                  className="bg-red-600"
                >
                  Usuń
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </CardContent>
    </Card>
  );
}
```

**Validation**:

- Pricing plans CRUD works
- Feature list editable
- Popular badge toggle works
- Responsive grid layout
- Delete confirmation working

---

### Task 044M: School Settings

**Files**:

- `components/features/cms/SchoolSettingsForm.tsx`

#### School Settings Form:

```typescript
// components/features/cms/SchoolSettingsForm.tsx
'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
  FormDescription,
} from '~/components/ui/form';
import { Input } from '~/components/ui/input';
import { Textarea } from '~/components/ui/textarea';
import { Button } from '~/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '~/components/ui/card';
import { Separator } from '~/components/ui/separator';
import { schoolSettingsSchema, type SchoolSettingsInput } from '~/lib/validations/cms';
import { api } from '~/utils/api';
import { useToast } from '~/hooks/use-toast';
import { Save, Building2, Mail, Phone, MapPin, Globe, FileText } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '~/components/ui/tabs';

export function SchoolSettingsForm() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();
  const utils = api.useUtils();

  const { data: settings, isLoading } = api.cms.getSchoolSettings.useQuery();

  const form = useForm<SchoolSettingsInput>({
    resolver: zodResolver(schoolSettingsSchema),
    values: settings || {
      schoolName: 'Na Piątkę',
      country: 'Polska',
    },
  });

  const updateMutation = api.cms.updateSchoolSettings.useMutation();

  const onSubmit = async (data: SchoolSettingsInput) => {
    setIsSubmitting(true);

    try {
      if (settings?.id) {
        await updateMutation.mutateAsync({ id: settings.id, ...data });
        toast({ title: 'Ustawienia zostały zaktualizowane' });
      }

      utils.cms.getSchoolSettings.invalidate();
    } catch (error: any) {
      toast({
        title: 'Błąd',
        description: error.message,
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return <div className="animate-pulse h-96 bg-gray-100 rounded-lg" />;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Ustawienia szkoły</CardTitle>
        <CardDescription>
          Zarządzaj podstawowymi informacjami o szkole
        </CardDescription>
      </CardHeader>

      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)}>
            <Tabs defaultValue="general" className="w-full">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="general">
                  <Building2 className="h-4 w-4 mr-2" />
                  Ogólne
                </TabsTrigger>
                <TabsTrigger value="contact">
                  <Mail className="h-4 w-4 mr-2" />
                  Kontakt
                </TabsTrigger>
                <TabsTrigger value="social">
                  <Globe className="h-4 w-4 mr-2" />
                  Social Media
                </TabsTrigger>
                <TabsTrigger value="business">
                  <FileText className="h-4 w-4 mr-2" />
                  Dane firmy
                </TabsTrigger>
              </TabsList>

              <TabsContent value="general" className="space-y-4 mt-6">
                <FormField
                  control={form.control}
                  name="schoolName"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Nazwa szkoły *</FormLabel>
                      <FormControl>
                        <Input {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="tagline"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Hasło przewodnie</FormLabel>
                      <FormControl>
                        <Input {...field} placeholder="np. Najlepsza szkoła korepetycji w mieście" />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="description"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Opis</FormLabel>
                      <FormControl>
                        <Textarea {...field} rows={4} placeholder="Krótki opis szkoły..." />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <div className="grid grid-cols-2 gap-4">
                  <FormField
                    control={form.control}
                    name="logoUrl"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>URL logo</FormLabel>
                        <FormControl>
                          <Input {...field} placeholder="https://..." />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="faviconUrl"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>URL favicon</FormLabel>
                        <FormControl>
                          <Input {...field} placeholder="https://..." />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
              </TabsContent>

              <TabsContent value="contact" className="space-y-4 mt-6">
                <div className="grid grid-cols-2 gap-4">
                  <FormField
                    control={form.control}
                    name="email"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Email</FormLabel>
                        <FormControl>
                          <Input {...field} type="email" />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="phone"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Telefon</FormLabel>
                        <FormControl>
                          <Input {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>

                <Separator />

                <FormField
                  control={form.control}
                  name="address"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Adres</FormLabel>
                      <FormControl>
                        <Input {...field} placeholder="ul. Przykładowa 123" />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <div className="grid grid-cols-3 gap-4">
                  <FormField
                    control={form.control}
                    name="city"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Miasto</FormLabel>
                        <FormControl>
                          <Input {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="postalCode"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Kod pocztowy</FormLabel>
                        <FormControl>
                          <Input {...field} placeholder="00-000" />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="country"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Kraj</FormLabel>
                        <FormControl>
                          <Input {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>

                <Separator />

                <div className="grid grid-cols-2 gap-4">
                  <FormField
                    control={form.control}
                    name="latitude"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Szerokość geograficzna</FormLabel>
                        <FormControl>
                          <Input
                            {...field}
                            type="number"
                            step="0.000001"
                            onChange={(e) => field.onChange(parseFloat(e.target.value))}
                          />
                        </FormControl>
                        <FormDescription>
                          Np. 52.229676 (dla mapy)
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="longitude"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Długość geograficzna</FormLabel>
                        <FormControl>
                          <Input
                            {...field}
                            type="number"
                            step="0.000001"
                            onChange={(e) => field.onChange(parseFloat(e.target.value))}
                          />
                        </FormControl>
                        <FormDescription>
                          Np. 21.012229 (dla mapy)
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
              </TabsContent>

              <TabsContent value="social" className="space-y-4 mt-6">
                <FormField
                  control={form.control}
                  name="facebook"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Facebook</FormLabel>
                      <FormControl>
                        <Input {...field} placeholder="https://facebook.com/..." />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="instagram"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Instagram</FormLabel>
                      <FormControl>
                        <Input {...field} placeholder="https://instagram.com/..." />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="linkedin"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>LinkedIn</FormLabel>
                      <FormControl>
                        <Input {...field} placeholder="https://linkedin.com/company/..." />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="youtube"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>YouTube</FormLabel>
                      <FormControl>
                        <Input {...field} placeholder="https://youtube.com/..." />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </TabsContent>

              <TabsContent value="business" className="space-y-4 mt-6">
                <FormField
                  control={form.control}
                  name="nip"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>NIP</FormLabel>
                      <FormControl>
                        <Input {...field} placeholder="123-456-78-90" />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="regon"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>REGON</FormLabel>
                      <FormControl>
                        <Input {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="krs"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>KRS</FormLabel>
                      <FormControl>
                        <Input {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </TabsContent>
            </Tabs>

            <Separator className="my-6" />

            <div className="flex justify-end">
              <Button type="submit" disabled={isSubmitting}>
                <Save className="h-4 w-4 mr-2" />
                {isSubmitting ? 'Zapisywanie...' : 'Zapisz ustawienia'}
              </Button>
            </div>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
```

**Validation**:

- All settings sections functional
- Form validation working
- Tabs navigation smooth
- Data persists correctly
- Coordinate inputs for map

---

### Task 044N: Google Maps API Integration

**Files**:

- `components/features/cms/GoogleMapsEmbed.tsx`
- `lib/google-maps.ts`

#### Google Maps Integration:

```bash
# Install Google Maps library
pnpm add @googlemaps/js-api-loader@^1.16.6
```

```typescript
// lib/google-maps.ts
import { Loader } from '@googlemaps/js-api-loader';

let googleMapsLoader: Loader | null = null;

export function getGoogleMapsLoader(): Loader {
  if (!googleMapsLoader) {
    googleMapsLoader = new Loader({
      apiKey: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY || '',
      version: 'weekly',
      libraries: ['places', 'geometry'],
    });
  }

  return googleMapsLoader;
}

export async function loadGoogleMaps() {
  const loader = getGoogleMapsLoader();
  return await loader.load();
}

export function generateGoogleMapsEmbedUrl(address: string): string {
  const encodedAddress = encodeURIComponent(address);
  return `https://www.google.com/maps/embed/v1/place?key=${process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY}&q=${encodedAddress}`;
}

export function generateGoogleMapsStaticUrl(
  latitude: number,
  longitude: number,
  zoom: number = 15,
  size: string = '600x400'
): string {
  return `https://maps.googleapis.com/maps/api/staticmap?center=${latitude},${longitude}&zoom=${zoom}&size=${size}&markers=color:red%7C${latitude},${longitude}&key=${process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY}`;
}
```

```typescript
// components/features/cms/GoogleMapsEmbed.tsx
'use client';

import { useEffect, useRef, useState } from 'react';
import { loadGoogleMaps } from '~/lib/google-maps';
import { Card, CardContent } from '~/components/ui/card';
import { Alert, AlertDescription } from '~/components/ui/alert';
import { MapPin } from 'lucide-react';

interface GoogleMapsEmbedProps {
  latitude: number;
  longitude: number;
  zoom?: number;
  height?: string;
  markerTitle?: string;
}

export function GoogleMapsEmbed({
  latitude,
  longitude,
  zoom = 15,
  height = '400px',
  markerTitle = 'Szkoła Korepetycji',
}: GoogleMapsEmbedProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const initMap = async () => {
      if (!mapRef.current) return;

      try {
        await loadGoogleMaps();

        const map = new google.maps.Map(mapRef.current, {
          center: { lat: latitude, lng: longitude },
          zoom: zoom,
          mapTypeControl: true,
          streetViewControl: true,
          fullscreenControl: true,
          zoomControl: true,
        });

        // Add marker
        new google.maps.Marker({
          position: { lat: latitude, lng: longitude },
          map: map,
          title: markerTitle,
          animation: google.maps.Animation.DROP,
        });

        // Add info window
        const infoWindow = new google.maps.InfoWindow({
          content: `<div style="padding: 8px;"><strong>${markerTitle}</strong></div>`,
        });

        const marker = new google.maps.Marker({
          position: { lat: latitude, lng: longitude },
          map: map,
          title: markerTitle,
        });

        marker.addListener('click', () => {
          infoWindow.open(map, marker);
        });

        setIsLoading(false);
      } catch (err) {
        console.error('Error loading Google Maps:', err);
        setError('Nie udało się załadować mapy. Sprawdź klucz API.');
        setIsLoading(false);
      }
    };

    initMap();
  }, [latitude, longitude, zoom, markerTitle]);

  if (error) {
    return (
      <Alert variant="destructive">
        <MapPin className="h-4 w-4" />
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  return (
    <Card>
      <CardContent className="p-0 relative">
        {isLoading && (
          <div
            className="absolute inset-0 flex items-center justify-center bg-gray-100 rounded-lg"
            style={{ height }}
          >
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
          </div>
        )}
        <div ref={mapRef} style={{ height, width: '100%' }} className="rounded-lg" />
      </CardContent>
    </Card>
  );
}
```

```typescript
// Add to SchoolSettingsForm.tsx - Map Preview Section
<Separator className="my-6" />

<div className="space-y-4">
  <h3 className="text-lg font-semibold">Podgląd mapy</h3>

  {form.watch('latitude') && form.watch('longitude') ? (
    <GoogleMapsEmbed
      latitude={form.watch('latitude')}
      longitude={form.watch('longitude')}
      markerTitle={form.watch('schoolName')}
    />
  ) : (
    <Alert>
      <MapPin className="h-4 w-4" />
      <AlertDescription>
        Uzupełnij współrzędne geograficzne aby zobaczyć podgląd mapy
      </AlertDescription>
    </Alert>
  )}
</div>
```

**Environment Variables**:

```bash
# Add to .env.local
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
```

**Validation**:

- Google Maps loads correctly
- Marker displays at correct location
- Interactive controls working
- API key properly configured
- Error handling functional

---

## ✅ SPRINT COMPLETION CHECKLIST

### Technical Validation

- [ ] All Prisma models created and migrated
- [ ] tRPC router fully implemented
- [ ] Zod validation schemas working
- [ ] Rich text editor functional
- [ ] Drag & drop working smoothly
- [ ] Image upload capability implemented
- [ ] Google Maps API integrated
- [ ] All CRUD operations working
- [ ] TypeScript types correct
- [ ] No console errors

### Feature Validation

- [ ] Admin can edit page content
- [ ] Team members CRUD works
- [ ] Drag & drop reordering functional
- [ ] Testimonial moderation works
- [ ] Pricing plans editable
- [ ] School settings persist
- [ ] Google Maps displays correctly
- [ ] Rich text formatting works
- [ ] All forms validate properly
- [ ] Delete confirmations working

### Integration Testing

- [ ] Database queries optimized
- [ ] tRPC API calls successful
- [ ] Real-time updates working
- [ ] Image URLs save correctly
- [ ] Coordinates save to database
- [ ] All relations working
- [ ] Transactions working properly

### UI/UX

- [ ] Responsive on all devices
- [ ] Loading states smooth
- [ ] Error messages clear
- [ ] Success toasts appearing
- [ ] Modal dialogs functional
- [ ] Forms user-friendly
- [ ] Drag handles visible
- [ ] Color pickers working

### Security & Performance

- [ ] Admin-only routes protected
- [ ] Input validation working
- [ ] XSS prevention in rich text
- [ ] SQL injection prevented (Prisma)
- [ ] File upload size limits
- [ ] Map loads efficiently
- [ ] Database indexes present
- [ ] No memory leaks

---

## 📊 SUCCESS METRICS

- **Functionality**: 100% of CMS features working
- **Usability**: Admin can manage all content without code
- **Performance**: <2s page load, <500ms mutations
- **Reliability**: Zero errors during normal operation
- **Integration**: Seamless public-facing content display

---

## 🔄 NEXT STEPS

After Sprint 2.4 completion:

1. **Sprint 3.1**: Admin Dashboard with statistics
2. **Sprint 3.2**: User management system
3. **Landing Page**: Use CMS data to render public site

---

**Sprint Completion**: All 7 tasks (044H-044N) completed and validated ✅
**Next Sprint**: Sprint 3.1 - Admin Dashboard & Analytics
**Coordination**: CMS provides data layer for landing page and admin panel
