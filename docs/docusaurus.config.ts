import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';

const config: Config = {
  title: 'KST Course Engine',
  tagline: 'Knowledge Space Theory — Formal Mathematical Structures for Adaptive Learning',
  favicon: 'img/favicon.ico',

  future: {
    v4: true,
  },

  url: 'https://kst-course-engine.vercel.app',
  baseUrl: '/',

  organizationName: 'gonzalezulises',
  projectName: 'kst-course-engine',

  onBrokenLinks: 'throw',

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          remarkPlugins: [remarkMath],
          rehypePlugins: [rehypeKatex],
          editUrl:
            'https://github.com/gonzalezulises/kst-course-engine/tree/main/docs/',
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  stylesheets: [
    {
      href: 'https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css',
      type: 'text/css',
      integrity: 'sha384-nB0miv6/jRmo5RLHW2XBgO+PKXu5iody3UJnT/sMock3Gs72yrOWoKz0Z2EY7bB',
      crossorigin: 'anonymous',
    },
  ],

  themeConfig: {
    image: 'img/docusaurus-social-card.jpg',
    colorMode: {
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: 'KST Course Engine',
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'theorySidebar',
          position: 'left',
          label: 'Theory',
        },
        {
          type: 'docSidebar',
          sidebarId: 'apiSidebar',
          position: 'left',
          label: 'API',
        },
        {
          type: 'docSidebar',
          sidebarId: 'researchSidebar',
          position: 'left',
          label: 'Research',
        },
        {
          href: 'https://github.com/gonzalezulises/kst-course-engine',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Documentation',
          items: [
            {
              label: 'Theory',
              to: '/docs/theory/knowledge-spaces',
            },
            {
              label: 'API Reference',
              to: '/docs/api/domain',
            },
          ],
        },
        {
          title: 'Research',
          items: [
            {
              label: 'Literature Review',
              to: '/docs/research/literature-review',
            },
            {
              label: 'Bibliography',
              to: '/docs/research/bibliography',
            },
          ],
        },
        {
          title: 'Development',
          items: [
            {
              label: 'Getting Started',
              to: '/docs/development/getting-started',
            },
            {
              label: 'GitHub',
              href: 'https://github.com/gonzalezulises/kst-course-engine',
            },
          ],
        },
      ],
      copyright: `Copyright ${new Date().getFullYear()} KST Course Engine. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['python', 'bash', 'yaml'],
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
