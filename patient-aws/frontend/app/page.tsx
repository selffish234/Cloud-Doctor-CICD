import { Hero } from "@/components/hero"
import { About } from "@/components/about"
import { Experience } from "@/components/experience"
import { Projects } from "@/components/projects"
import { Certifications } from "@/components/certifications"
import { Contact } from "@/components/contact"
import { Navigation } from "@/components/navigation"
import { Volunteer } from "@/components/volunteer"
import { CloudDoctorSection } from "@/components/cloud-doctor-section"

export default function Home() {
  return (
    <main className="min-h-screen bg-background">
      <Navigation />
      <Hero />
      <About />
      <Experience />
      <Projects />
      <CloudDoctorSection />
      <Volunteer />
      <Certifications />
      <Contact />
    </main>
  )
}
