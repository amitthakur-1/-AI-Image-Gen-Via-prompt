# ImagineAI - AI Image Generation Frontend

A modern, premium AI image generation frontend built with React.js, Vite, and Tailwind CSS. Features a sleek dark theme with glassmorphism effects, smooth animations, and a professional SaaS-like interface.

## 🚀 Features

- **Modern UI/UX**: Dark theme with purple/blue gradients and glassmorphism effects
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile
- **Smooth Animations**: Powered by Framer Motion
- **AI Image Generation**: Connects to backend API for generating images from prompts
- **Advanced Controls**: Width/height selectors, CFG scale, steps, seed, model selection
- **Style Presets**: Pre-built prompts for different art styles (Realistic, Anime, Cinematic, etc.)
- **Image Gallery**: Masonry grid layout with hover effects
- **Fullscreen Viewer**: Detailed image preview with generation settings
- **History Panel**: View and manage previously generated images
- **Keyboard Shortcuts**: Ctrl+Enter to generate, Ctrl+K to clear
- **Copy to Clipboard**: Easy prompt copying and sharing
- **Download Images**: High-quality image downloads
- **Loading States**: Beautiful animated loaders and progress bars

## 🛠️ Tech Stack

- **Frontend Framework**: React 19
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **Animations**: Framer Motion
- **Icons**: Lucide React
- **HTTP Client**: Axios
- **State Management**: Zustand
- **Notifications**: React Hot Toast
- **Routing**: React Router

## 📁 Project Structure

```
src/
├── assets/                 # Static assets
├── components/
│   ├── common/            # Reusable UI components
│   ├── layout/            # Layout components (Navbar, Sidebar, etc.)
│   ├── generator/         # Image generation components
│   ├── gallery/           # Image gallery and viewer
│   └── history/           # History and management
├── pages/                 # Page components
├── hooks/                 # Custom React hooks
├── services/              # API services
├── store/                 # Zustand store
├── utils/                 # Utility functions
├── constants/             # App constants and config
├── data/                  # Static data
├── context/               # React context providers
└── styles/                # Additional styles
```

## 🚀 Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd imagineai
```

2. Install dependencies:

```bash
npm install
```

3. Start the development server:

```bash
npm run dev
```

4. Open [http://localhost:5173](http://localhost:5173) in your browser

### Build for Production

```bash
npm run build
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
VITE_API_BASE_URL=http://localhost:3001/api
```

### API Integration

The frontend expects a backend API with the following endpoint:

```
POST /generate-image
```

Request body:

```json
{
  "prompt": "A beautiful sunset...",
  "negative_prompt": "blurry, low quality...",
  "width": 512,
  "height": 512,
  "steps": 30,
  "cfg_scale": 7,
  "seed": 12345,
  "model": "stable-diffusion-xl",
  "num_images": 1
}
```

Response:

```json
{
  "images": [
    {
      "url": "https://...",
      "id": "generated-id"
    }
  ]
}
```

## 🎨 Customization

### Theme Colors

Colors are defined in `tailwind.config.js`:

```js
colors: {
  primary: { /* Purple/blue gradient */ },
  secondary: { /* Accent colors */ },
  dark: { /* Dark theme colors */ }
}
```

### Animations

Customize animations in `src/index.css` or add new ones using Framer Motion.

## 📱 Responsive Design

- **Desktop**: 3-column layout with sidebar
- **Tablet**: Responsive grid with collapsible sidebar
- **Mobile**: Single column with bottom navigation

## ⌨️ Keyboard Shortcuts

- `Ctrl + Enter`: Generate image
- `Ctrl + K`: Clear prompts
- `Escape`: Close fullscreen modal

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- Design inspiration from Midjourney, Leonardo AI, and Playground AI
- Built with modern React patterns and best practices
- Focus on user experience and performance

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.
