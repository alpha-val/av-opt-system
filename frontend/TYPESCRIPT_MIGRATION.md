# TypeScript Migration Guide

This document outlines the TypeScript migration for the frontend application.

## ✅ Completed

### Configuration
- ✅ Added TypeScript dependencies to `package.json`
- ✅ Created `tsconfig.json` with proper configuration
- ✅ Updated `webpack.config.js` to support TypeScript/TSX files
- ✅ Added Babel preset for TypeScript

### Type Definitions
- ✅ Created `src/types/api.ts` with API type definitions matching backend schemas
- ✅ Types for: `ProjectCreate`, `ProjectUpdate`, `ProjectOut`, `ApiError`, etc.

### Converted Files
- ✅ `src/index.jsx` → `src/index.tsx`
- ✅ `src/App.jsx` → `src/App.tsx`
- ✅ `src/components/Nav.jsx` → `src/components/Nav.tsx`
- ✅ `src/views/dashboard/Dashboard.jsx` → `src/views/dashboard/Dashboard.tsx`
- ✅ `src/views/project/ProjectList.jsx` → `src/views/project/ProjectList.tsx`

### New Files
- ✅ `src/services/api.ts` - Typed API service for project operations

## 📋 Remaining Files to Convert

### High Priority
- [ ] `src/redux/store.jsx` → `src/redux/store.ts`
- [ ] `src/redux/authSlice.jsx` → `src/redux/authSlice.ts`
- [ ] `src/redux/userSlice.jsx` → `src/redux/userSlice.ts`
- [ ] `src/components/LogoutButton.jsx` → `src/components/LogoutButton.tsx`
- [ ] `src/services/AuthProvider.jsx` → `src/services/AuthProvider.tsx`
- [ ] `src/themes/ThemeContext.jsx` → `src/themes/ThemeContext.tsx`
- [ ] `src/hooks/DialogsProvider.jsx` → `src/hooks/DialogsProvider.tsx`
- [ ] `src/views/NotFound.jsx` → `src/views/NotFound.tsx`

### Medium Priority
- [ ] Other view components
- [ ] Hook files
- [ ] Utility files

## 🚀 Next Steps

1. **Install Dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Run Type Check**
   ```bash
   npx tsc --noEmit
   ```

3. **Start Development Server**
   ```bash
   npm start
   ```

## 📝 TypeScript Best Practices

### Type Safety
- Always define interfaces for component props
- Use `React.FC<Props>` for functional components
- Prefer `interface` over `type` for object shapes
- Use union types for limited value sets

### API Types
- Keep `src/types/api.ts` in sync with backend schemas
- Use the types from `api.ts` in API service calls
- Add JSDoc comments for complex types

### Component Props
```typescript
interface MyComponentProps {
  title: string;
  count?: number;
  onAction: (id: string) => void;
}

const MyComponent: React.FC<MyComponentProps> = ({ title, count, onAction }) => {
  // ...
};
```

### Redux Types
When converting Redux slices, use:
```typescript
import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface MyState {
  // ...
}

const mySlice = createSlice({
  name: 'mySlice',
  initialState: {} as MyState,
  reducers: {
    // ...
  },
});
```

## 🔧 Configuration Details

### tsconfig.json
- `strict: true` - Enables all strict type checking
- `allowJs: true` - Allows gradual migration (JS and TS files together)
- `jsx: "react-jsx"` - Uses new JSX transform
- `paths` - Configured for `@/*` alias (can be used for imports)

### Webpack
- Handles both `.ts` and `.tsx` files
- Uses Babel for transpilation
- Source maps enabled for debugging

## ⚠️ Notes

- Old `.jsx` files can coexist with `.tsx` files during migration
- TypeScript will check `.tsx` files but not `.jsx` files
- Gradually convert files as you work on them
- Use `// @ts-ignore` or `// @ts-expect-error` sparingly and document why

## 🐛 Troubleshooting

### Common Issues

1. **Module not found errors**
   - Check file extensions in imports
   - Ensure `tsconfig.json` paths are correct

2. **Type errors from third-party libraries**
   - Install `@types/package-name` if available
   - Check if types are included in the package

3. **Material-UI type issues**
   - Material-UI v7 includes TypeScript types
   - Use `@mui/material` types directly

## 📚 Resources

- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)
- [React TypeScript Cheatsheet](https://react-typescript-cheatsheet.netlify.app/)
- [Redux Toolkit TypeScript Guide](https://redux-toolkit.js.org/usage/usage-with-typescript)

