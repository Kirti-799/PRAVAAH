/**
 * frontend/src/pages/LandingPage.tsx
 *
 * Official Landing Page for PRAVAAH — AI-Powered Flood Risk Assessment & Management System.
 * Visual Direction:
 * - Deep navy blue (#182746) for header, hero overlay, and footer.
 * - Light aqua (#C8E5E5) for feature and content section backgrounds.
 * - Teal (#119E9A) for primary interactive buttons and icons.
 * - Clean white (#FFFFFF) card surfaces with dark blue-grey (#2B3A4A) typography.
 * - Curved wave bottom edge on hero transitioning into the light aqua features section.
 */

import React, { useState } from 'react';
import {
  CloudSun,
  Activity,
  ShieldAlert,
  MapPin,
  Users,
  Compass,
  ArrowRight,
  ChevronDown,
  Menu,
  X,
  ShieldCheck,
  CheckCircle2,
} from 'lucide-react';
import heroFloodImage from '../assets/hero_flood.jpg';

interface LandingPageProps {
  onGetStarted: () => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onGetStarted }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const scrollToSection = (id: string) => {
    setMobileMenuOpen(false);
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="h-full w-full overflow-y-auto overflow-x-hidden bg-[#F5F9F9] text-[#2B3A4A] scroll-smooth">
      {/* ========================================================================= */}
      {/* 1. HEADER                                                                */}
      {/* ========================================================================= */}
      <header className="sticky top-0 z-50 w-full bg-[#182746] text-white shadow-md">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          {/* Brand Logo & Name */}
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#119E9A] text-white shadow-sm">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div>
              <span className="text-lg font-bold tracking-tight text-white sm:text-xl">
                PRAVAAH
              </span>
              <span className="hidden lg:inline text-xs text-[#C8E5E5]/80 ml-2 font-light">
                | Flood Risk Assessment & Management System
              </span>
            </div>
          </div>

          {/* Desktop Navigation Links */}
          <nav className="hidden md:flex items-center gap-8 text-sm font-medium">
            <button
              type="button"
              onClick={() => scrollToSection('home')}
              className="text-[#C8E5E5] hover:text-white transition-colors"
            >
              Home
            </button>
            <button
              type="button"
              onClick={() => scrollToSection('features')}
              className="text-[#C8E5E5] hover:text-white transition-colors"
            >
              Features
            </button>
            <button
              type="button"
              onClick={() => scrollToSection('how-it-works')}
              className="text-[#C8E5E5] hover:text-white transition-colors"
            >
              How It Works
            </button>
            <button
              type="button"
              onClick={() => scrollToSection('about')}
              className="text-[#C8E5E5] hover:text-white transition-colors"
            >
              About
            </button>
            <button
              type="button"
              onClick={onGetStarted}
              className="flex items-center gap-1.5 rounded-full bg-[#119E9A] px-5 py-2 text-sm font-semibold text-white shadow-sm hover:bg-[#0E8582] active:scale-98 transition-all"
            >
              <span>Get Started</span>
              <ArrowRight className="h-4 w-4" />
            </button>
          </nav>

          {/* Mobile Menu Button */}
          <div className="flex md:hidden">
            <button
              type="button"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="rounded-md p-2 text-[#C8E5E5] hover:bg-[#25345B] hover:text-white"
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
          </div>
        </div>

        {/* Mobile Dropdown Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-[#25345B] bg-[#182746] px-4 pt-2 pb-5 space-y-3">
            <button
              type="button"
              onClick={() => scrollToSection('home')}
              className="block w-full text-left py-2 text-sm font-medium text-[#C8E5E5] hover:text-white"
            >
              Home
            </button>
            <button
              type="button"
              onClick={() => scrollToSection('features')}
              className="block w-full text-left py-2 text-sm font-medium text-[#C8E5E5] hover:text-white"
            >
              Features
            </button>
            <button
              type="button"
              onClick={() => scrollToSection('how-it-works')}
              className="block w-full text-left py-2 text-sm font-medium text-[#C8E5E5] hover:text-white"
            >
              How It Works
            </button>
            <button
              type="button"
              onClick={() => scrollToSection('about')}
              className="block w-full text-left py-2 text-sm font-medium text-[#C8E5E5] hover:text-white"
            >
              About
            </button>
            <button
              type="button"
              onClick={onGetStarted}
              className="flex w-full items-center justify-center gap-2 rounded-full bg-[#119E9A] py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-[#0E8582]"
            >
              <span>Get Started</span>
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        )}
      </header>

      {/* ========================================================================= */}
      {/* 2. HERO SECTION                                                           */}
      {/* ========================================================================= */}
      <section
        id="home"
        className="relative min-h-[580px] sm:min-h-[640px] w-full bg-[#182746] flex flex-col justify-between overflow-hidden"
      >
        {/* Background Aerial Photograph with Subtle Zoom */}
        <div className="absolute inset-0 overflow-hidden">
          <img
            src={heroFloodImage}
            alt="Aerial view of flood waters and river plain"
            className="h-full w-full object-cover object-center animate-hero-zoom opacity-45 scale-105"
          />
          {/* Deep Navy Gradient Overlay ensuring strong text contrast */}
          <div className="absolute inset-0 bg-gradient-to-b from-[#182746]/85 via-[#182746]/75 to-[#182746]" />
        </div>

        {/* Hero Content Container */}
        <div className="relative z-10 mx-auto flex max-w-4xl flex-1 flex-col items-center justify-center px-4 pt-16 pb-12 text-center sm:px-6 lg:px-8">
          <div className="animate-fade-in-up space-y-6">
            {/* System Identifier Badge */}
            <div className="inline-flex items-center gap-2 rounded-full border border-[#119E9A]/50 bg-[#119E9A]/15 px-4 py-1.5 text-xs font-semibold text-[#C8E5E5] backdrop-blur-xs">
              <span className="h-2 w-2 rounded-full bg-[#119E9A]" />
              <span>Upper-to-Middle Yamuna Floodplain Intelligence</span>
            </div>

            {/* Main Headline */}
            <h1 className="text-3xl font-extrabold tracking-tight text-white sm:text-5xl lg:text-6xl max-w-3xl leading-tight">
              Predicting Flood Risks. Supporting Safer Decisions.
            </h1>

            {/* Description */}
            <p className="mx-auto max-w-2xl text-sm sm:text-base lg:text-lg leading-relaxed text-[#C8E5E5]/90 font-light">
              PRAVAAH combines weather forecasts, historical flood information and geographical intelligence to assess potential flood risks and support informed disaster preparedness.
            </p>

            {/* Hero Action Buttons */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
              <button
                type="button"
                onClick={onGetStarted}
                className="w-full sm:w-auto flex items-center justify-center gap-2 rounded-full bg-[#119E9A] px-8 py-3.5 text-base font-bold text-white shadow-lg hover:bg-[#0E8582] active:scale-98 transition-all"
              >
                <span>Get Started</span>
                <ArrowRight className="h-5 w-5" />
              </button>

              <button
                type="button"
                onClick={() => scrollToSection('features')}
                className="w-full sm:w-auto flex items-center justify-center rounded-full border border-white/60 bg-white/10 px-8 py-3.5 text-base font-semibold text-white backdrop-blur-xs hover:bg-white/20 transition-all"
              >
                Explore Features
              </button>
            </div>
          </div>
        </div>

        {/* Scroll Down Chevron */}
        <div className="relative z-10 flex flex-col items-center pb-2 text-[#C8E5E5]/80">
          <button
            type="button"
            onClick={() => scrollToSection('features')}
            aria-label="Scroll to features"
            className="hover:text-white transition-colors"
          >
            <ChevronDown className="h-6 w-6 animate-bounce" />
          </button>
        </div>

        {/* Distinctive Curved Wave Bottom Edge transitioning into Light Aqua (#C8E5E5) */}
        <div className="relative w-full overflow-hidden leading-none z-10">
          <svg
            className="relative block w-full h-14 sm:h-20 md:h-28 text-[#C8E5E5] fill-current"
            viewBox="0 0 1440 120"
            preserveAspectRatio="none"
          >
            <path d="M0,0 C480,120 960,120 1440,0 L1440,120 L0,120 Z" />
          </svg>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 3. FEATURES SECTION (Light Aqua Background #C8E5E5)                       */}
      {/* ========================================================================= */}
      <section
        id="features"
        className="w-full bg-[#C8E5E5] py-16 sm:py-20 px-4 sm:px-6 lg:px-8"
      >
        <div className="mx-auto max-w-7xl">
          {/* Section Heading */}
          <div className="text-center max-w-2xl mx-auto space-y-2 mb-12 sm:mb-16">
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-[#182746] tracking-tight">
              Intelligent Tools for Flood Preparedness
            </h2>
            <p className="text-sm sm:text-base text-[#25345B] font-medium">
              Explore the capabilities of PRAVAAH.
            </p>
          </div>

          {/* 6 Feature Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8">
            {/* Card 1: Weather Forecasting */}
            <div className="rounded-xl bg-[#FFFFFF] p-6 shadow-sm hover:shadow-md hover:-translate-y-1 transition-all duration-300 flex flex-col justify-between border border-[#A8D4D4]/40">
              <div className="space-y-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-[#E6F5F5] text-[#119E9A]">
                  <CloudSun className="h-6 w-6" />
                </div>
                <h3 className="text-lg font-bold text-[#182746]">
                  Weather Forecasting
                </h3>
                <p className="text-sm text-[#2B3A4A] leading-relaxed">
                  Access available weather forecasts and rainfall information.
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-[#EAF2F2] flex items-center text-xs font-semibold text-[#119E9A]">
                <span>Open-Meteo Integration</span>
              </div>
            </div>

            {/* Card 2: Historical Flood Data */}
            <div className="rounded-xl bg-[#FFFFFF] p-6 shadow-sm hover:shadow-md hover:-translate-y-1 transition-all duration-300 flex flex-col justify-between border border-[#A8D4D4]/40">
              <div className="space-y-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-[#E6F5F5] text-[#119E9A]">
                  <Activity className="h-6 w-6" />
                </div>
                <h3 className="text-lg font-bold text-[#182746]">
                  Historical Flood Data
                </h3>
                <p className="text-sm text-[#2B3A4A] leading-relaxed">
                  Explore historical rainfall, river discharge and flood events.
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-[#EAF2F2] flex items-center text-xs font-semibold text-[#119E9A]">
                <span>2018–2025 Hydrometric Archive</span>
              </div>
            </div>

            {/* Card 3: Flood Risk Assessment */}
            <div className="rounded-xl bg-[#FFFFFF] p-6 shadow-sm hover:shadow-md hover:-translate-y-1 transition-all duration-300 flex flex-col justify-between border border-[#A8D4D4]/40">
              <div className="space-y-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-[#E6F5F5] text-[#119E9A]">
                  <ShieldAlert className="h-6 w-6" />
                </div>
                <h3 className="text-lg font-bold text-[#182746]">
                  Flood Risk Assessment
                </h3>
                <p className="text-sm text-[#2B3A4A] leading-relaxed">
                  Assess potential flood risk for selected geographical areas.
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-[#EAF2F2] flex items-center text-xs font-semibold text-[#119E9A]">
                <span>Coupled ML & CWC Thresholds</span>
              </div>
            </div>

            {/* Card 4: Interactive Risk Mapping */}
            <div className="rounded-xl bg-[#FFFFFF] p-6 shadow-sm hover:shadow-md hover:-translate-y-1 transition-all duration-300 flex flex-col justify-between border border-[#A8D4D4]/40">
              <div className="space-y-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-[#E6F5F5] text-[#119E9A]">
                  <MapPin className="h-6 w-6" />
                </div>
                <h3 className="text-lg font-bold text-[#182746]">
                  Interactive Risk Mapping
                </h3>
                <p className="text-sm text-[#2B3A4A] leading-relaxed">
                  Visualize low, moderate and high-risk areas geographically.
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-[#EAF2F2] flex items-center text-xs font-semibold text-[#119E9A]">
                <span>Green / Orange / Red Classifications</span>
              </div>
            </div>

            {/* Card 5: Population Impact Assessment */}
            <div className="rounded-xl bg-[#FFFFFF] p-6 shadow-sm hover:shadow-md hover:-translate-y-1 transition-all duration-300 flex flex-col justify-between border border-[#A8D4D4]/40">
              <div className="space-y-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-[#E6F5F5] text-[#119E9A]">
                  <Users className="h-6 w-6" />
                </div>
                <h3 className="text-lg font-bold text-[#182746]">
                  Population Impact Assessment
                </h3>
                <p className="text-sm text-[#2B3A4A] leading-relaxed">
                  Estimate potentially exposed populations using available spatial data.
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-[#EAF2F2] flex items-center text-xs font-semibold text-[#119E9A]">
                <span>Floodplain Khadar Exposure</span>
              </div>
            </div>

            {/* Card 6: Evacuation Assistance */}
            <div className="rounded-xl bg-[#FFFFFF] p-6 shadow-sm hover:shadow-md hover:-translate-y-1 transition-all duration-300 flex flex-col justify-between border border-[#A8D4D4]/40">
              <div className="space-y-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-[#E6F5F5] text-[#119E9A]">
                  <Compass className="h-6 w-6" />
                </div>
                <h3 className="text-lg font-bold text-[#182746]">
                  Evacuation Assistance
                </h3>
                <p className="text-sm text-[#2B3A4A] leading-relaxed">
                  Explore candidate evacuation locations and available shelter information.
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-[#EAF2F2] flex items-center text-xs font-semibold text-[#119E9A]">
                <span>Candidate Municipal Relocation Centres</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 4. HOW IT WORKS SECTION                                                   */}
      {/* ========================================================================= */}
      <section
        id="how-it-works"
        className="w-full bg-[#FFFFFF] py-16 sm:py-20 px-4 sm:px-6 lg:px-8 border-t border-b border-[#D8ECEC]"
      >
        <div className="mx-auto max-w-7xl">
          <div className="text-center max-w-2xl mx-auto space-y-2 mb-12">
            <span className="text-xs font-bold uppercase tracking-wider text-[#119E9A]">
              Simple 4-Step Process
            </span>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-[#182746] tracking-tight">
              How PRAVAAH Works
            </h2>
            <p className="text-sm text-[#5A6A7E]">
              From geographical selection to actionable disaster preparedness in seconds.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Step 1 */}
            <div className="relative rounded-xl border border-[#D8ECEC] bg-[#F5F9F9] p-5 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#119E9A] text-white text-sm font-bold">
                  1
                </div>
                <span className="text-[11px] font-mono text-[#5A6A7E]">Area Setup</span>
              </div>
              <h3 className="font-bold text-[#182746] text-base">Select Geographical Area</h3>
              <p className="text-xs text-[#2B3A4A] leading-relaxed">
                Choose a Yamuna river reach, upstream basin, or corridor station through the dropdown or interactive map.
              </p>
            </div>

            {/* Step 2 */}
            <div className="relative rounded-xl border border-[#D8ECEC] bg-[#F5F9F9] p-5 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#119E9A] text-white text-sm font-bold">
                  2
                </div>
                <span className="text-[11px] font-mono text-[#5A6A7E]">Horizon</span>
              </div>
              <h3 className="font-bold text-[#182746] text-base">Choose Forecast Period</h3>
              <p className="text-xs text-[#2B3A4A] leading-relaxed">
                Select an operational horizon between 2 and 10 days with transparent confidence indicators.
              </p>
            </div>

            {/* Step 3 */}
            <div className="relative rounded-xl border border-[#D8ECEC] bg-[#F5F9F9] p-5 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#119E9A] text-white text-sm font-bold">
                  3
                </div>
                <span className="text-[11px] font-mono text-[#5A6A7E]">Inference</span>
              </div>
              <h3 className="font-bold text-[#182746] text-base">Assess Flood Risk</h3>
              <p className="text-xs text-[#2B3A4A] leading-relaxed">
                Backend ML models predict upstream inflow, paired with live meteorological forecasts and official CWC flood thresholds.
              </p>
            </div>

            {/* Step 4 */}
            <div className="relative rounded-xl border border-[#D8ECEC] bg-[#F5F9F9] p-5 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#119E9A] text-white text-sm font-bold">
                  4
                </div>
                <span className="text-[11px] font-mono text-[#5A6A7E]">Action</span>
              </div>
              <h3 className="font-bold text-[#182746] text-base">Explore Zones & Shelters</h3>
              <p className="text-xs text-[#2B3A4A] leading-relaxed">
                Inspect Green, Orange, and Red risk reaches on the Leaflet map and review candidate evacuation centres.
              </p>
            </div>
          </div>

          <div className="mt-10 text-center">
            <button
              type="button"
              onClick={onGetStarted}
              className="inline-flex items-center gap-2 rounded-full bg-[#119E9A] px-7 py-3 text-sm font-bold text-white shadow-md hover:bg-[#0E8582] transition-colors"
            >
              <span>Launch Assessment Workspace</span>
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 5. ABOUT SECTION                                                          */}
      {/* ========================================================================= */}
      <section
        id="about"
        className="w-full bg-[#F5F9F9] py-16 sm:py-20 px-4 sm:px-6 lg:px-8"
      >
        <div className="mx-auto max-w-4xl space-y-8">
          <div className="text-center space-y-3">
            <span className="text-xs font-bold uppercase tracking-wider text-[#119E9A]">
              Platform Overview
            </span>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-[#182746] tracking-tight">
              About PRAVAAH
            </h2>
            <p className="text-sm sm:text-base text-[#2B3A4A] leading-relaxed">
              PRAVAAH is a flood risk assessment and management platform designed to combine weather information, historical hydrological data and geographical analysis to support better-informed flood preparedness and response.
            </p>
          </div>

          {/* Three Key Architectural Pillars */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5 pt-4 text-xs">
            <div className="rounded-lg bg-white p-4 border border-[#D8ECEC] space-y-1.5 shadow-2xs">
              <span className="flex items-center gap-1.5 font-bold text-[#182746]">
                <CheckCircle2 className="h-4 w-4 text-[#119E9A]" />
                Scientific Honesty
              </span>
              <p className="text-[#5A6A7E] leading-relaxed">
                Clear distinction between upstream ML discharge predictions, rule-based flood classifications, and restricted downstream gauge data.
              </p>
            </div>

            <div className="rounded-lg bg-white p-4 border border-[#D8ECEC] space-y-1.5 shadow-2xs">
              <span className="flex items-center gap-1.5 font-bold text-[#182746]">
                <CheckCircle2 className="h-4 w-4 text-[#119E9A]" />
                Authentic Geography
              </span>
              <p className="text-[#5A6A7E] leading-relaxed">
                11,365 km² Copernicus DEM catchment basin paired with 268.9 km OpenStreetMap Yamuna mainstem river geometry.
              </p>
            </div>

            <div className="rounded-lg bg-white p-4 border border-[#D8ECEC] space-y-1.5 shadow-2xs">
              <span className="flex items-center gap-1.5 font-bold text-[#182746]">
                <CheckCircle2 className="h-4 w-4 text-[#119E9A]" />
                Civilian Usability
              </span>
              <p className="text-[#5A6A7E] leading-relaxed">
                Streamlined 3-tier risk classifications (Green, Orange, Red) and candidate evacuation locations without technical GIS jargon.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 6. FOOTER                                                                 */}
      {/* ========================================================================= */}
      <footer className="w-full bg-[#182746] text-[#C8E5E5] py-12 px-4 sm:px-6 lg:px-8 border-t border-[#25345B]">
        <div className="mx-auto max-w-7xl flex flex-col md:flex-row items-start md:items-center justify-between gap-8">
          <div className="space-y-2 max-w-md">
            <div className="flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded bg-[#119E9A] text-white">
                <ShieldCheck className="h-4 w-4" />
              </div>
              <span className="font-extrabold text-white tracking-tight text-lg">
                PRAVAAH
              </span>
            </div>
            <p className="text-xs text-[#C8E5E5]/80 leading-relaxed">
              AI-Powered Flood Risk Assessment & Management System focusing on the Upper-to-Middle Yamuna River Corridor from Hathnikund Barrage to Delhi.
            </p>
          </div>

          <div className="flex flex-wrap gap-6 text-xs font-medium">
            <button
              type="button"
              onClick={() => scrollToSection('home')}
              className="text-[#C8E5E5] hover:text-white transition-colors"
            >
              Home
            </button>
            <button
              type="button"
              onClick={() => scrollToSection('features')}
              className="text-[#C8E5E5] hover:text-white transition-colors"
            >
              Features
            </button>
            <button
              type="button"
              onClick={() => scrollToSection('how-it-works')}
              className="text-[#C8E5E5] hover:text-white transition-colors"
            >
              How It Works
            </button>
            <button
              type="button"
              onClick={() => scrollToSection('about')}
              className="text-[#C8E5E5] hover:text-white transition-colors"
            >
              About
            </button>
            <button
              type="button"
              onClick={onGetStarted}
              className="font-bold text-[#119E9A] hover:underline"
            >
              Open System Workspace →
            </button>
          </div>
        </div>

        <div className="mx-auto max-w-7xl mt-8 pt-6 border-t border-[#25345B] flex flex-col sm:flex-row items-center justify-between text-[11px] text-[#C8E5E5]/60 gap-3">
          <div>
            © 2026 PRAVAAH. All rights reserved. Meteorological data powered by Open-Meteo API.
          </div>
          <div>
            Candidate shelter facilities are illustrative planning prototypes.
          </div>
        </div>
      </footer>
    </div>
  );
};

