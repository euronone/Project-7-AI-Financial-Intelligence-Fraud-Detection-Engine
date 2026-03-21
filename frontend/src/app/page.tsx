"use client";

import React from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  ShieldAlert,
  Zap,
  Network,
  Activity,
  ArrowRight,
  CheckCircle2,
  Lock,
  Cpu,
  Globe,
  Database,
  Server
} from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans selection:bg-blue-200">
      {/* Navigation */}
      <nav className="fixed top-0 w-full bg-white/80 backdrop-blur-md border-b border-slate-200 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2">
              <ShieldAlert className="h-8 w-8 text-blue-600" />
              <span className="font-bold text-xl tracking-tight">FinShield AI</span>
            </div>
            <div className="hidden md:flex items-center gap-8 text-sm font-medium">
              <Link href="#features" className="text-slate-600 hover:text-blue-600 transition-colors">Features</Link>
              <Link href="#how-it-works" className="text-slate-600 hover:text-blue-600 transition-colors">How it Works</Link>
              <Link href="#architecture" className="text-slate-600 hover:text-blue-600 transition-colors">Architecture</Link>
              <Link href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer" className="text-slate-600 hover:text-blue-600 transition-colors">API Docs</Link>
            </div>
            <div className="flex items-center gap-4">
              <Link href="/login" className="text-sm font-medium text-slate-600 hover:text-blue-600 transition-colors">
                Sign In
              </Link>
              <Link href="/login" className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-all shadow-sm hover:shadow-md">
                Request Demo
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="text-center max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <span className="inline-block py-1 px-3 rounded-full bg-blue-100 text-blue-700 text-xs font-semibold tracking-wider uppercase mb-6 border border-blue-200">
              Next-Generation Fraud Prevention
            </span>
            <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-slate-900 mb-8 leading-tight">
              Stop complex fraud in <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600">sub-200ms</span>
            </h1>
            <p className="text-xl text-slate-600 mb-10 leading-relaxed max-w-3xl mx-auto">
              A real-time, hybrid decision engine combining deterministic rules with advanced machine learning to detect sophisticated financial crime while reducing false positives.
            </p>
            <div className="flex flex-col sm:flex-row justify-center gap-4">
              <Link href="/login" className="flex items-center justify-center gap-2 bg-blue-600 text-white px-8 py-4 rounded-xl text-lg font-medium hover:bg-blue-700 transition-all shadow-lg hover:shadow-xl hover:-translate-y-0.5">
                Request a Demo <ArrowRight className="w-5 h-5" />
              </Link>
              <Link href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer" className="flex items-center justify-center gap-2 bg-white text-slate-700 border border-slate-300 px-8 py-4 rounded-xl text-lg font-medium hover:bg-slate-50 transition-all">
                View API Docs
              </Link>
            </div>
          </motion.div>
        </div>

        {/* Hero Image/Dashboard Preview */}
        <motion.div 
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.2 }}
          className="mt-20 relative mx-auto max-w-5xl"
        >
          <div className="absolute inset-0 bg-gradient-to-t from-slate-50 via-transparent to-transparent z-10 h-full w-full"></div>
          <div className="rounded-2xl border border-slate-200 bg-white shadow-2xl overflow-hidden">
            <div className="border-b border-slate-100 bg-slate-50/50 px-4 py-3 flex items-center gap-2">
              <div className="flex gap-1.5">
                <div className="w-3 h-3 rounded-full bg-red-400"></div>
                <div className="w-3 h-3 rounded-full bg-amber-400"></div>
                <div className="w-3 h-3 rounded-full bg-green-400"></div>
              </div>
              <div className="mx-auto bg-white border border-slate-200 rounded-md px-32 py-1 flex items-center gap-2">
                <Lock className="w-3 h-3 text-slate-400" />
                <span className="text-xs text-slate-500 font-mono">finshield.ai/dashboard</span>
              </div>
            </div>
            {/* Mock Dashboard UI */}
            <div className="p-6 grid grid-cols-12 gap-6 bg-slate-50/30">
              {/* Sidebar */}
              <div className="col-span-3 space-y-4">
                <div className="h-8 w-3/4 bg-slate-200 rounded animate-pulse"></div>
                <div className="space-y-2 pt-4">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <div key={i} className="h-6 w-full bg-slate-100 rounded"></div>
                  ))}
                </div>
              </div>
              {/* Main Content */}
              <div className="col-span-9 space-y-6">
                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                    <div className="text-sm text-slate-500 mb-1">Transactions Monitored</div>
                    <div className="text-2xl font-bold">1.2M</div>
                    <div className="text-xs text-green-600 mt-1 flex items-center gap-1">+14% today</div>
                  </div>
                  <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                    <div className="text-sm text-slate-500 mb-1">Fraud Blocked</div>
                    <div className="text-2xl font-bold text-blue-600">$4.3M</div>
                    <div className="text-xs text-green-600 mt-1 flex items-center gap-1">+2% today</div>
                  </div>
                  <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                    <div className="text-sm text-slate-500 mb-1">Avg Latency</div>
                    <div className="text-2xl font-bold">42ms</div>
                    <div className="text-xs text-green-600 mt-1 flex items-center gap-1">P95: 110ms</div>
                  </div>
                </div>
                <div className="bg-white h-64 rounded-xl border border-slate-200 shadow-sm p-4 flex flex-col justify-end gap-2 relative overflow-hidden">
                  {/* Mock Chart */}
                  <div className="absolute top-4 left-4 text-sm font-medium text-slate-700">Risk Score Distribution</div>
                  <div className="flex items-end gap-2 h-3/4 w-full px-4">
                    {[40, 60, 80, 50, 90, 100, 70, 40, 30, 80, 110, 60, 40, 20].map((h, i) => (
                      <div key={i} className="flex-1 bg-blue-100 rounded-t-sm" style={{ height: `${h}%` }}>
                        <div className="w-full bg-blue-500 rounded-t-sm" style={{ height: `${h * 0.7}%` }}></div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Stats Row */}
        <div className="mt-20 grid grid-cols-2 md:grid-cols-4 gap-8 max-w-4xl mx-auto border-y border-slate-200 py-10">
          <div className="text-center">
            <div className="text-3xl font-bold text-slate-900 mb-1">{"< 200ms"}</div>
            <div className="text-sm text-slate-500">Decision Latency</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-slate-900 mb-1">99.99%</div>
            <div className="text-sm text-slate-500">Platform Uptime</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-slate-900 mb-1">40%</div>
            <div className="text-sm text-slate-500">Fewer False Positives</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-slate-900 mb-1">200+</div>
            <div className="text-sm text-slate-500">Engineered Features</div>
          </div>
        </div>
      </section>

      {/* Problem/Solution Section */}
      <section className="py-24 bg-white" id="problem">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-2 gap-16 items-center">
            <div>
              <h2 className="text-3xl font-bold mb-6">Traditional rules engines are failing.</h2>
              <p className="text-lg text-slate-600 mb-6">
                Legacy fraud systems rely entirely on static rules, resulting in massive operational overhead, unacceptable false positive rates, and an inability to adapt to novel fraud patterns like synthetic identity creation and complex money mule networks.
              </p>
              <ul className="space-y-4">
                <li className="flex gap-3">
                  <div className="flex-shrink-0 w-6 h-6 rounded-full bg-red-100 flex items-center justify-center mt-1">
                    <div className="w-2 h-2 rounded-full bg-red-600"></div>
                  </div>
                  <div>
                    <h4 className="font-semibold text-slate-900">High False Positives</h4>
                    <p className="text-slate-600 text-sm">Blocking legitimate customers ruins user experience and costs revenue.</p>
                  </div>
                </li>
                <li className="flex gap-3">
                  <div className="flex-shrink-0 w-6 h-6 rounded-full bg-red-100 flex items-center justify-center mt-1">
                    <div className="w-2 h-2 rounded-full bg-red-600"></div>
                  </div>
                  <div>
                    <h4 className="font-semibold text-slate-900">Slow Adaptation</h4>
                    <p className="text-slate-600 text-sm">Writing new rules takes days while fraudsters pivot in hours.</p>
                  </div>
                </li>
              </ul>
            </div>
            <div className="bg-slate-50 p-8 rounded-2xl border border-slate-200">
              <h3 className="text-2xl font-bold mb-6 text-blue-900">The FinShield AI Advantage</h3>
              <p className="text-slate-600 mb-8">
                We combine the deterministic control of a modern rules engine with the adaptive power of machine learning ensembles.
              </p>
              <div className="space-y-4">
                <div className="flex items-center gap-4 bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                  <div className="bg-blue-100 p-3 rounded-lg text-blue-600"><Cpu className="w-6 h-6" /></div>
                  <div>
                    <div className="font-semibold">Hybrid Decisioning</div>
                    <div className="text-sm text-slate-500">Rules + ML Models working in parallel</div>
                  </div>
                </div>
                <div className="flex items-center gap-4 bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                  <div className="bg-indigo-100 p-3 rounded-lg text-indigo-600"><Network className="w-6 h-6" /></div>
                  <div>
                    <div className="font-semibold">Behavioral & Network Profiling</div>
                    <div className="text-sm text-slate-500">Understand the entity, not just the transaction</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-24 bg-slate-50" id="features">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Comprehensive Fraud Defense</h2>
            <p className="text-lg text-slate-600">
              Everything you need to detect, investigate, and prevent financial crime across your platform.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
              <div className="w-12 h-12 bg-blue-100 text-blue-600 rounded-xl flex items-center justify-center mb-6">
                <Zap className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold mb-3">Real-Time Scoring</h3>
              <p className="text-slate-600 mb-4 text-sm leading-relaxed">
                Score transactions in milliseconds. Ingest via REST API for sync flows or Azure Event Hubs for high-throughput async processing.
              </p>
              <ul className="space-y-2 text-sm text-slate-500">
                <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-green-500" /> Sub-200ms P95 latency</li>
                <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-green-500" /> 200+ engineered features</li>
              </ul>
            </div>

            {/* Feature 2 */}
            <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
              <div className="w-12 h-12 bg-indigo-100 text-indigo-600 rounded-xl flex items-center justify-center mb-6">
                <Cpu className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold mb-3">Advanced ML Models</h3>
              <p className="text-slate-600 mb-4 text-sm leading-relaxed">
                Ensemble models (XGBoost + Neural Networks) combined with Isolation Forests to catch both known patterns and novel anomalies.
              </p>
              <ul className="space-y-2 text-sm text-slate-500">
                <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-green-500" /> ONNX Runtime serving</li>
                <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-green-500" /> SHAP explainability</li>
              </ul>
            </div>

            {/* Feature 3 */}
            <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
              <div className="w-12 h-12 bg-purple-100 text-purple-600 rounded-xl flex items-center justify-center mb-6">
                <Activity className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold mb-3">Dynamic Rules Engine</h3>
              <p className="text-slate-600 mb-4 text-sm leading-relaxed">
                Write deterministic rules via UI or API. Support for complex AND/OR logic, velocity checks, and pre-built templates.
              </p>
              <ul className="space-y-2 text-sm text-slate-500">
                <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-green-500" /> Dry-run testing</li>
                <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-green-500" /> Priority-based execution</li>
              </ul>
            </div>

            {/* Feature 4 */}
            <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
              <div className="w-12 h-12 bg-emerald-100 text-emerald-600 rounded-xl flex items-center justify-center mb-6">
                <Network className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold mb-3">Entity & Network Analysis</h3>
              <p className="text-slate-600 mb-4 text-sm leading-relaxed">
                Move beyond transaction-level scoring. Build behavioral baselines for entities and detect fraud rings via graph analysis.
              </p>
              <ul className="space-y-2 text-sm text-slate-500">
                <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-green-500" /> Entity 360 views</li>
                <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-green-500" /> Cross-account link detection</li>
              </ul>
            </div>

            {/* Feature 5 */}
            <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
              <div className="w-12 h-12 bg-orange-100 text-orange-600 rounded-xl flex items-center justify-center mb-6">
                <ShieldAlert className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold mb-3">Case Management</h3>
              <p className="text-slate-600 mb-4 text-sm leading-relaxed">
                Built-in ticketing and investigation workflows for your analyst team. Auto-assign alerts based on severity and rules.
              </p>
              <ul className="space-y-2 text-sm text-slate-500">
                <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-green-500" /> Real-time Socket.IO alerts</li>
                <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-green-500" /> Automated evidence gathering</li>
              </ul>
            </div>

            {/* Feature 6 */}
            <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
              <div className="w-12 h-12 bg-cyan-100 text-cyan-600 rounded-xl flex items-center justify-center mb-6">
                <Globe className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold mb-3">Omnichannel Integrations</h3>
              <p className="text-slate-600 mb-4 text-sm leading-relaxed">
                Seamlessly connect with your existing stack via webhooks, external sanctions lists (OFAC), and notification providers.
              </p>
              <ul className="space-y-2 text-sm text-slate-500">
                <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-green-500" /> Secure Webhooks w/ HMAC</li>
                <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-green-500" /> Twilio & SendGrid ready</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Architecture / How it works */}
      <section className="py-24 bg-slate-900 text-white" id="architecture">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Enterprise-Grade Architecture</h2>
            <p className="text-lg text-slate-400">
              Built on Next.js, FastAPI, and PostgreSQL. Designed for scale, security, and strict compliance.
            </p>
          </div>

          <div className="grid md:grid-cols-4 gap-4 text-center">
            <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 relative">
              <Database className="w-8 h-8 text-blue-400 mx-auto mb-4" />
              <h4 className="font-bold mb-2">1. Ingestion</h4>
              <p className="text-sm text-slate-400">REST API or Azure Event Hubs streams transactions.</p>
              <ArrowRight className="hidden md:block absolute -right-3 top-1/2 -translate-y-1/2 text-slate-600 w-6 h-6" />
            </div>
            <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 relative">
              <Server className="w-8 h-8 text-indigo-400 mx-auto mb-4" />
              <h4 className="font-bold mb-2">2. Processing</h4>
              <p className="text-sm text-slate-400">Feature engineering & Redis cache lookups.</p>
              <ArrowRight className="hidden md:block absolute -right-3 top-1/2 -translate-y-1/2 text-slate-600 w-6 h-6" />
            </div>
            <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 relative">
              <Cpu className="w-8 h-8 text-purple-400 mx-auto mb-4" />
              <h4 className="font-bold mb-2">3. Decisioning</h4>
              <p className="text-sm text-slate-400">Parallel execution of Rules Engine & ML Models.</p>
              <ArrowRight className="hidden md:block absolute -right-3 top-1/2 -translate-y-1/2 text-slate-600 w-6 h-6" />
            </div>
            <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
              <ShieldAlert className="w-8 h-8 text-emerald-400 mx-auto mb-4" />
              <h4 className="font-bold mb-2">4. Action</h4>
              <p className="text-sm text-slate-400">Composite risk score generated. Webhooks & alerts fired.</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 bg-white relative overflow-hidden">
        <div className="absolute inset-0 bg-blue-50/50"></div>
        <div className="max-w-4xl mx-auto px-4 relative z-10 text-center">
            <h2 className="text-4xl font-bold mb-6">Ready to secure your transactions?</h2>
          <p className="text-xl text-slate-600 mb-10">
            Join leading financial institutions using FinShield AI to stop fraud before it happens.
          </p>
          <div className="flex flex-col sm:flex-row justify-center gap-4">
            <Link href="/login" className="bg-blue-600 text-white px-8 py-4 rounded-xl text-lg font-medium hover:bg-blue-700 transition-all shadow-lg hover:shadow-xl hover:-translate-y-0.5">
              Request a Demo
            </Link>
            <Link href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer" className="bg-white text-slate-700 border border-slate-300 px-8 py-4 rounded-xl text-lg font-medium hover:bg-slate-50 transition-all">
              Read the API Docs
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-900 text-slate-400 py-12 border-t border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 grid md:grid-cols-4 gap-8 mb-12">
          <div className="col-span-1 md:col-span-2">
            <div className="flex items-center gap-2 mb-4">
              <ShieldAlert className="h-6 w-6 text-blue-500" />
              <span className="font-bold text-lg text-white">FinShield AI</span>
            </div>
            <p className="text-sm mb-6 max-w-sm">
              Enterprise-grade financial intelligence and fraud detection engine. Securing the future of digital finance.
            </p>
            <div className="text-xs">
              &copy; {new Date().getFullYear()} FinShield AI. All rights reserved.
            </div>
          </div>
          
          <div>
            <h4 className="text-white font-semibold mb-4">Product</h4>
            <ul className="space-y-2 text-sm">
              <li><Link href="#features" className="hover:text-white transition-colors">Features</Link></li>
              <li><Link href="#architecture" className="hover:text-white transition-colors">Architecture</Link></li>
              <li><Link href="/pricing" className="hover:text-white transition-colors">Pricing</Link></li>
              <li><Link href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">API Documentation</Link></li>
            </ul>
          </div>
          
          <div>
            <h4 className="text-white font-semibold mb-4">Legal & Compliance</h4>
            <ul className="space-y-2 text-sm">
              <li><Link href="/privacy" className="hover:text-white transition-colors">Privacy Policy</Link></li>
              <li><Link href="/terms" className="hover:text-white transition-colors">Terms of Service</Link></li>
              <li><Link href="/security" className="hover:text-white transition-colors">Security (SOC 2)</Link></li>
            </ul>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8 border-t border-slate-800">
          <h4 className="text-white font-semibold mb-4 text-center">Team Credits</h4>
          <div className="flex flex-wrap justify-center gap-x-4 gap-y-2 text-xs text-slate-500 max-w-4xl mx-auto text-center">
            <span>Sudhanshu</span>
            <span>&bull;</span>
            <span>Anu L Sasidharan</span>
            <span>&bull;</span>
            <span>Sunil Gupta</span>
            <span>&bull;</span>
            <span>Manish Mishra</span>
            <span>&bull;</span>
            <span>chidi henry</span>
            <span>&bull;</span>
            <span>Naveen Srikakolapu</span>
            <span>&bull;</span>
            <span>Makwana shivam</span>
            <span>&bull;</span>
            <span>Naveen V</span>
            <span>&bull;</span>
            <span>Yogi</span>
            <span>&bull;</span>
            <span>Sanjay Kumar</span>
            <span>&bull;</span>
            <span>Prodip sarkar</span>
            <span>&bull;</span>
            <span>Sumit Kumar</span>
            <span>&bull;</span>
            <span>Rajiv Ranjan</span>
            <span>&bull;</span>
            <span>shewan Dagne</span>
            <span>&bull;</span>
            <span>Dnyaneshwar Bhosale</span>
            <span>&bull;</span>
            <span>Abhrajit Pal</span>
            <span>&bull;</span>
            <span>Narender Kumar</span>
            <span>&bull;</span>
            <span>pallavi sindkar</span>
            <span>&bull;</span>
            <span>Rajesh S</span>
            <span>&bull;</span>
            <span>Manju</span>
            <span>&bull;</span>
            <span>Susil padhy</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
