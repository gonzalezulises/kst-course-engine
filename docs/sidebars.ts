import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  theorySidebar: [
    'intro',
    {
      type: 'category',
      label: 'Theory',
      items: [
        'theory/knowledge-spaces',
        'theory/surmise-relations',
        'theory/learning-spaces',
        'theory/knowledge-assessment',
        'theory/algorithmic-analysis',
        'theory/optimization-theory',
      ],
    },
    {
      type: 'category',
      label: 'Development',
      items: [
        'development/getting-started',
        'development/testing-strategy',
        'development/contributing',
        'development/cli',
        'development/api-quickstart',
        'development/examples',
      ],
    },
  ],
  apiSidebar: [
    {
      type: 'category',
      label: 'API Reference',
      items: [
        'api/domain',
        'api/space',
        'api/prerequisites',
        'api/validation',
        'api/parser',
        'api/assessment',
        'api/estimation',
        'api/learning',
        'api/viz',
        'api/interactive',
        'api/optimization',
        'api/rest-api',
      ],
    },
  ],
  researchSidebar: [
    {
      type: 'category',
      label: 'Research',
      items: [
        'research/literature-review',
        'research/novel-contributions',
        'research/bibliography',
      ],
    },
  ],
};

export default sidebars;
