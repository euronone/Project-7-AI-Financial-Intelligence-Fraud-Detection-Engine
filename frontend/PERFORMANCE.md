# Frontend Performance Optimization Guide - FinShield AI

> **Target**: Achieve Lighthouse scores ≥90 on Performance, Accessibility, Best Practices, and SEO

## 🚀 Performance Metrics

### Core Web Vitals
- **Largest Contentful Paint (LCP)**: < 2.5s (green)
- **First Input Delay (FID)**: < 100ms (green)
- **Cumulative Layout Shift (CLS)**: < 0.1 (green)

### Additional Metrics
- **First Contentful Paint (FCP)**: < 1.8s
- **Time to Interactive (TTI)**: < 3.8s
- **Total Blocking Time (TBT)**: < 200ms

## 📦 Bundling Optimizations

### 1. Code Splitting
- **Automatic Route-based Splitting**: Next.js splits per route automatically
- **Dynamic Imports**: Use `React.lazy()` for non-critical components
- **Component-level Splitting**: Lazy load heavy components (charts, modals)

```typescript
// Example: Lazy load dashboard charts
import dynamic from 'next/dynamic';

const FraudTrendsChart = dynamic(() => import('@/components/charts/FraudTrends'), {
  loading: () => <ChartSkeleton />,
  ssr: false, // Disable SSR for client-only charts
});
```

### 2. Webpack Configuration
- **Tree Shaking**: Enabled by default in production builds
- **Chunk Splitting**: Vendor, common, and page-specific chunks
- **Module Federation**: Share code between applications (if needed)
- **Dynamic Imports**: Webpack 5 native support in Next.js 12+

### 3. JavaScript Optimization
- **Minification**: SWC minification (faster than Terser)
- **Compression**: Brotli compression on server
- **Source Maps**: Disabled in production for smaller builds
- **Dead Code Elimination**: Tree-shaking removes unused code

## 🖼️ Image Optimization

### Next.js Image Component
```typescript
import Image from 'next/image';

<Image
  src="/fraud-icon.png"
  alt="Fraud detection icon"
  width={48}
  height={48}
  priority={false} // Use true only for above-fold images
  loading="lazy" // Default: lazy loading
  quality={75} // Balance quality/size
/>
```

### Image Best Practices
- Use WebP format (with JPEG fallback)
- Use appropriate image sizes (avoid 4k images for 48px thumbnails)
- Use SVG for icons and illustrations
- Compress images before uploading
- Use AVIF format for modern browsers

### Recommended Tools
- [TinyPNG](https://tinypng.com/): Batch image compression
- [Squoosh](https://squoosh.app/): Format conversion
- [ImageOptim](https://imageoptim.com/): Mac image optimization

## ⚡ Runtime Optimizations

### 1. React Performance
- **Memoization**: Use `React.memo()` for expensive components
- **useCallback**: Memoize callbacks passed to memoized components
- **useMemo**: Cache expensive computations
- **Virtual Scrolling**: For long lists (use `react-window`)
- **Server Components**: Offload logic to server

```typescript
// Example: Memoized component
const TransactionRow = React.memo(({ txn }) => (
  <tr>{/* content */}</tr>
), (prev, next) => prev.id === next.id); // Custom comparison
```

### 2. Data Fetching
- **API Response Caching**: Cache API responses with stale-while-revalidate
- **SWR/React Query**: Automatic caching, refetching, deduplication
- **Pagination**: Never load all data at once
- **GraphQL**: Consider for complex data queries

```typescript
import useSWR from 'swr';

const { data, error } = useSWR('/api/transactions', fetcher, {
  revalidateOnFocus: false,
  dedupingInterval: 60000, // 1 minute deduplication
});
```

### 3. Bundle Size Analysis
```bash
# Analyze bundle size
npm install --save-dev @next/bundle-analyzer

# Usage in next.config.ts
import withBundleAnalyzer from '@next/bundle-analyzer';

export default withBundleAnalyzer({
  enabled: process.env.ANALYZE === 'true',
})(nextConfig);

# Run analysis
ANALYZE=true npm run build
```

## 🎬 Animation Performance

### 1. Hardware Acceleration
- Use `transform` and `opacity` for animations (GPU-accelerated)
- Avoid animating properties like `width`, `height`, `left`, `top`
- Use `will-change` CSS property sparingly

```css
.animated-element {
  will-change: transform, opacity;
  animation: slide 0.5s ease-out;
}

@keyframes slide {
  from {
    transform: translateX(-100px);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}
```

### 2. Framer Motion Optimization
- Reduce animation complexity for lower-end devices
- Use `reducedMotion` for accessibility
- Profile animations with DevTools Performance tab

```typescript
const motionVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.3 } },
};
```

## 🔍 Monitoring Performance

### 1. Built-in Tools
- **Chrome DevTools**: Performance tab, Lighthouse audits
- **Next.js Analytics**: Built-in Web Vitals monitoring
- **Vercel Analytics**: Real user monitoring if deployed on Vercel

### 2. Performance Budget
```json
{
  "bundles": [
    {
      "name": "main",
      "maxSize": "150kb"
    },
    {
      "name": "landing",
      "maxSize": "100kb"
    }
  ]
}
```

### 3. Continuous Monitoring
```bash
# Generate Lighthouse report
npm run audit

# Expected scores
# Performance: >90
# Accessibility: >95
# Best Practices: >90
# SEO: >90
```

## 🎯 Optimization Checklist

### Critical (must do)
- [ ] Images optimized and using Next.js Image component
- [ ] Code splitting enabled for routes
- [ ] Third-party scripts deferred or async
- [ ] CSS minified and unused rules removed
- [ ] Animations use transform/opacity only
- [ ] No layout shift during loading

### Important (should do)
- [ ] API responses cached
- [ ] Heavy components lazy-loaded
- [ ] JavaScript bundles analyzed
- [ ] Long tasks broken into smaller chunks
- [ ] Accessibility standards met
- [ ] Mobile performance tested

### Nice to have
- [ ] Server-side rendering where beneficial
- [ ] Progressive Web App features
- [ ] Service worker caching strategy
- [ ] Font subsetting and optimization
- [ ] Critical CSS inlined

## 📊 Performance Reporting

Generate performance reports regularly:

```bash
# Install lighthouse CLI
npm install -g lighthouse

# Generate report
lighthouse https://finshield.local --output=html --output-path=./report.html

# View in browser
open report.html
```

## 🔗 Resources

- [Web Vitals Guide](https://web.dev/vitals/)
- [Next.js Performance](https://nextjs.org/learn/foundations/how-nextjs-works/rendering)
- [Chrome DevTools Performance](https://developer.chrome.com/docs/devtools/performance/)
- [Lighthouse Documentation](https://developers.google.com/web/tools/lighthouse)
- [React Performance](https://react.dev/reference/react/memo)
