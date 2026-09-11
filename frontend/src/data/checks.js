import {
  BookOpenText,
  Captions,
  Chrome,
  Gauge,
  Image,
  Languages,
  LayoutDashboard,
  Link2,
  List,
  Files,
  Mail,
  MessageCircle,
  PanelTop,
  SearchCheck,
  Share2,
  Sparkles,
} from "lucide-react";


export const CHECKS = [
  {
    id: "page_speed",
    label: "Page Speed",
    category: "Performance",
    icon: Gauge,
  },
  {
    id: "links",
    label: "Broken Links",
    category: "Site Integrity",
    icon: Link2,
  },
  {
    id: "page_link_list",
    label: "Page Link List",
    category: "Site Integrity",
    icon: List,
  },
  {
    id: "website_page_list",
    label: "Website Page List",
    category: "Site Integrity",
    icon: Files,
  },
  {
    id: "images",
    label: "Image Optimization",
    category: "Site Integrity",
    icon: Image,
  },
  {
    id: "meta",
    label: "Meta & Source Data",
    category: "SEO",
    icon: SearchCheck,
  },
  {
    id: "sticky_header",
    label: "Sticky Header",
    category: "Layout",
    icon: PanelTop,
  },
  {
    id: "css_animation",
    label: "CSS Animation",
    category: "Experience",
    icon: Sparkles,
  },
  {
    id: "browser_compatibility",
    label: "Browser Compatibility",
    category: "Compatibility",
    icon: Chrome,
  },
  {
    id: "google_translate",
    label: "Google Translate",
    category: "Functionality",
    icon: Languages,
  },
  {
    id: "whatsapp",
    label: "WhatsApp",
    category: "Functionality",
    icon: MessageCircle,
  },
  {
    id: "social_media",
    label: "Social Media",
    category: "Functionality",
    icon: Share2,
  },
  {
    id: "contact_form",
    label: "Contact Form",
    category: "Functionality",
    icon: Mail,
  },
  {
    id: "blog",
    label: "Blog Page",
    category: "Content",
    icon: BookOpenText,
  },
  {
    id: "content",
    label: "Content & Spelling",
    category: "Content",
    icon: Captions,
  },
  {
    id: "layout_design",
    label: "Layout & Design",
    category: "Layout",
    icon: LayoutDashboard,
  },
];


export const ALL_CHECK_IDS =
  CHECKS.map(
    (check) => check.id
  );
