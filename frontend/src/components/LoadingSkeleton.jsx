import { Skeleton, Stack, Group, SimpleGrid, Box } from '@mantine/core';

function LoadingSkeleton({ type = 'default', count = 1 }) {
  if (type === 'dashboard') {
    return (
      <Box p="md">
        <Group justify="space-between" mb="xl">
          <Skeleton height={40} width={200} />
          <Skeleton height={36} width={120} />
        </Group>

        <SimpleGrid cols={4} spacing="lg" mb="xl" breakpoints={[
          { maxWidth: 'md', cols: 2 },
          { maxWidth: 'sm', cols: 1 },
        ]}>
          {[...Array(4)].map((_, i) => (
            <Box key={i} p="md" style={{ border: '1px solid var(--card-border)', borderRadius: '8px' }}>
              <Group>
                <Skeleton height={40} circle />
                <Stack spacing="xs" style={{ flex: 1 }}>
                  <Skeleton height={16} width="60%" />
                  <Skeleton height={24} width="40%" />
                </Stack>
              </Group>
            </Box>
          ))}
        </SimpleGrid>

        <SimpleGrid cols={2} spacing="lg" breakpoints={[{ maxWidth: 'sm', cols: 1 }]}>
          <Box>
            <Skeleton height={28} width={150} mb="md" />
            <Stack spacing="md">
              {[...Array(3)].map((_, i) => (
                <Skeleton key={i} height={80} />
              ))}
            </Stack>
          </Box>
          <Box>
            <Skeleton height={28} width={150} mb="md" />
            <Stack spacing="md">
              {[...Array(3)].map((_, i) => (
                <Skeleton key={i} height={60} />
              ))}
            </Stack>
          </Box>
        </SimpleGrid>
      </Box>
    );
  }

  if (type === 'device-list') {
    return (
      <Box p="md">
        <Group justify="space-between" mb="xl">
          <Skeleton height={40} width={200} />
          <Skeleton height={36} width={120} />
        </Group>
        <SimpleGrid cols={3} spacing="lg" breakpoints={[
          { maxWidth: 'md', cols: 2 },
          { maxWidth: 'sm', cols: 1 },
        ]}>
          {[...Array(count)].map((_, i) => (
            <Box key={i} p="md" style={{ border: '1px solid var(--card-border)', borderRadius: '8px' }}>
              <Skeleton height={24} mb="md" />
              <Skeleton height={60} mb="md" />
              <Skeleton height={20} />
            </Box>
          ))}
        </SimpleGrid>
      </Box>
    );
  }

  if (type === 'device-detail') {
    return (
      <Box p="md">
        <Group justify="space-between" mb="xl">
          <Skeleton height={40} width={250} />
          <Group>
            <Skeleton height={36} width={80} />
            <Skeleton height={36} width={120} />
          </Group>
        </Group>

        <SimpleGrid cols={4} spacing="lg" mb="xl" breakpoints={[
          { maxWidth: 'md', cols: 2 },
          { maxWidth: 'sm', cols: 1 },
        ]}>
          {[...Array(4)].map((_, i) => (
            <Box key={i} p="md" style={{ border: '1px solid var(--card-border)', borderRadius: '8px' }}>
              <Group>
                <Skeleton height={32} circle />
                <Stack spacing="xs" style={{ flex: 1 }}>
                  <Skeleton height={14} />
                  <Skeleton height={18} width="70%" />
                </Stack>
              </Group>
            </Box>
          ))}
        </SimpleGrid>

        <Stack spacing="xl">
          {[...Array(3)].map((_, i) => (
            <Box key={i}>
              <Skeleton height={28} width={180} mb="md" />
              <Skeleton height={120} />
            </Box>
          ))}
        </Stack>
      </Box>
    );
  }

  // Default skeleton
  return (
    <Stack spacing="md" p="md">
      {[...Array(count)].map((_, i) => (
        <Skeleton key={i} height={20} />
      ))}
    </Stack>
  );
}

export default LoadingSkeleton;
