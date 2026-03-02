import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const episodes = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/data/episodes' }),
  schema: z.object({
    title: z.string(),
    date: z.coerce.date(),
    audio: z.string(),
    num: z.union([z.number(), z.string()]).optional(),
  }),
});

export const collections = { episodes };
