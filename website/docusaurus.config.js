// @ts-check
// Docusaurus 3.x configuration for the tethysext-atcore documentation site.

const { themes: prismThemes } = require('prism-react-renderer');

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'tethysext-atcore',
  tagline: 'A Tethys Platform extension providing reusable controllers, services, and gizmos.',
  favicon: 'img/favicon.ico',

  url: 'https://aquaveo.github.io',
  baseUrl: '/tethysext-atcore/',

  organizationName: 'Aquaveo',
  projectName: 'tethysext-atcore',

  trailingSlash: false,
  onBrokenLinks: 'throw',
  markdown: {
    hooks: {
      onBrokenMarkdownLinks: 'warn',
    },
  },

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          routeBasePath: '/',
          sidebarPath: require.resolve('./sidebars.js'),
          editUrl: 'https://github.com/Aquaveo/tethysext-atcore/edit/master/website/',
        },
        blog: false,
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      navbar: {
        title: 'tethysext-atcore',
        items: [
          {
            type: 'docSidebar',
            sidebarId: 'tutorialSidebar',
            position: 'left',
            label: 'Docs',
          },
          {
            type: 'docSidebar',
            sidebarId: 'apiSidebar',
            position: 'left',
            label: 'API',
          },
          {
            href: 'https://github.com/Aquaveo/tethysext-atcore',
            label: 'GitHub',
            position: 'right',
          },
        ],
      },
      footer: {
        style: 'light',
        links: [
          {
            title: 'Project',
            items: [
              {
                label: 'GitHub',
                href: 'https://github.com/Aquaveo/tethysext-atcore',
              },
              {
                label: 'License',
                href: 'https://github.com/Aquaveo/tethysext-atcore/blob/master/LICENSE',
              },
            ],
          },
        ],
        copyright: `Copyright \u00a9 ${new Date().getFullYear()} Aquaveo, LLC. Built with Docusaurus.`,
      },
      prism: {
        theme: prismThemes.github,
        darkTheme: prismThemes.dracula,
        additionalLanguages: ['bash', 'python', 'json', 'yaml'],
      },
    }),
};

module.exports = config;
