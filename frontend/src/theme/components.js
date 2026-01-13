// Component style overrides for Mantine components

export const components = {
  Card: {
    defaultProps: {
      shadow: 'sm',
      padding: 'lg',
      radius: 'md',
      withBorder: true,
    },
    styles: (theme) => ({
      root: {
        backgroundColor: theme.colorScheme === 'dark'
          ? theme.colors.dark[7]
          : theme.white,
        borderColor: theme.colorScheme === 'dark'
          ? theme.colors.dark[4]
          : theme.colors.gray[3],
        transition: 'transform 0.2s ease, box-shadow 0.2s ease',
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: theme.shadows.md,
        },
      },
    }),
  },

  Button: {
    defaultProps: {
      radius: 'md',
    },
    styles: (theme) => ({
      root: {
        fontWeight: 500,
        transition: 'all 0.2s ease',
      },
    }),
  },

  Badge: {
    defaultProps: {
      radius: 'sm',
      size: 'md',
      variant: 'filled',
    },
    styles: (theme) => ({
      root: {
        fontWeight: 600,
        letterSpacing: '0.5px',
        textTransform: 'uppercase',
        fontSize: theme.fontSizes.xs,
      },
    }),
  },

  Table: {
    defaultProps: {
      striped: true,
      highlightOnHover: true,
      withBorder: true,
      withColumnBorders: false,
    },
    styles: (theme) => ({
      root: {
        borderColor: theme.colorScheme === 'dark'
          ? theme.colors.dark[4]
          : theme.colors.gray[3],
      },
    }),
  },

  Modal: {
    defaultProps: {
      centered: true,
      radius: 'md',
      overlayProps: {
        opacity: 0.55,
        blur: 3,
      },
    },
    styles: (theme) => ({
      content: {
        backgroundColor: theme.colorScheme === 'dark'
          ? theme.colors.dark[7]
          : theme.white,
      },
      header: {
        backgroundColor: theme.colorScheme === 'dark'
          ? theme.colors.dark[6]
          : theme.colors.gray[0],
      },
    }),
  },

  TextInput: {
    defaultProps: {
      radius: 'md',
    },
    styles: (theme) => ({
      input: {
        backgroundColor: theme.colorScheme === 'dark'
          ? theme.colors.dark[8]
          : theme.white,
        borderColor: theme.colorScheme === 'dark'
          ? theme.colors.dark[4]
          : theme.colors.gray[3],
        '&:focus': {
          borderColor: theme.colors[theme.primaryColor][6],
        },
      },
    }),
  },

  Select: {
    defaultProps: {
      radius: 'md',
    },
    styles: (theme) => ({
      input: {
        backgroundColor: theme.colorScheme === 'dark'
          ? theme.colors.dark[8]
          : theme.white,
        borderColor: theme.colorScheme === 'dark'
          ? theme.colors.dark[4]
          : theme.colors.gray[3],
        '&:focus': {
          borderColor: theme.colors[theme.primaryColor][6],
        },
      },
    }),
  },

  Paper: {
    defaultProps: {
      shadow: 'xs',
      padding: 'md',
      radius: 'md',
      withBorder: true,
    },
    styles: (theme) => ({
      root: {
        backgroundColor: theme.colorScheme === 'dark'
          ? theme.colors.dark[7]
          : theme.white,
        borderColor: theme.colorScheme === 'dark'
          ? theme.colors.dark[4]
          : theme.colors.gray[3],
      },
    }),
  },

  Alert: {
    defaultProps: {
      radius: 'md',
    },
  },

  Skeleton: {
    styles: (theme) => ({
      root: {
        '&::before': {
          background: theme.colorScheme === 'dark'
            ? theme.colors.dark[5]
            : theme.colors.gray[2],
        },
        '&::after': {
          background: theme.colorScheme === 'dark'
            ? `linear-gradient(90deg, transparent, ${theme.colors.dark[4]}, transparent)`
            : `linear-gradient(90deg, transparent, ${theme.colors.gray[0]}, transparent)`,
        },
      },
    }),
  },

  Container: {
    defaultProps: {
      sizes: {
        xs: 540,
        sm: 720,
        md: 960,
        lg: 1200,
        xl: 1200, // Match current max-width
      },
    },
  },
};
