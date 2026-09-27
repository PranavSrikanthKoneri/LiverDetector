import { useEffect, useRef, useState } from "react";
import { ArrowRightIcon, ArrowDownIcon, InfoCircledIcon } from "@radix-ui/react-icons";
import ScanIllustration from "../components/ScanIllustration";
import { designVariant } from "../design/variant";
import "./LandingPage.css";

const chapters = [
  { label: "Locate", title: "Start with the liver.", text: "A selected outline brings the liver into focus. Inspect the scan and its mask, side by side with the measurements." },
  { label: "Measure", title: "Look a little closer.", text: "Explore the two-echo fat estimate and texture entropy: a description of how varied image patterns are within the sampled liver." },
  { label: "Understand", title: "Keep the context.", text: "See imaging measurements alongside the questionnaire risk estimate. Explore population-based projections, with the original scan always available." },
];

export default function LandingPage({ onStart }) {
  const root = useRef(null);
  const story = useRef(null);
  const [chapter, setChapter] = useState(0);
  const { visual, motion } = designVariant;
  const real = visual === "mri";

  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    let frame;
    function update() {
      if (!root.current || !story.current) return;
      const rect = story.current.getBoundingClientRect();
      const progress = Math.max(0, Math.min(1, (window.innerHeight * 0.25 - rect.top) / Math.max(1, rect.height - window.innerHeight * 0.6)));
      root.current.style.setProperty("--story-progress", media.matches ? 0 : progress);
      root.current.style.setProperty("--hero-progress", media.matches ? 0 : Math.min(1, window.scrollY / window.innerHeight));
      if (!media.matches) {
        const articles = [...story.current.querySelectorAll(".story-chapter")];
        const distances = articles.map(article => {
          const bounds = article.getBoundingClientRect();
          return Math.abs(bounds.top + bounds.height / 2 - window.innerHeight / 2);
        });
        setChapter(distances.indexOf(Math.min(...distances)));
      }
    }
    function schedule() { cancelAnimationFrame(frame); frame = requestAnimationFrame(update); }
    update();
    window.addEventListener("scroll", schedule, { passive: true });
    window.addEventListener("resize", schedule);
    media.addEventListener("change", schedule);
    return () => { cancelAnimationFrame(frame); window.removeEventListener("scroll", schedule); window.removeEventListener("resize", schedule); media.removeEventListener("change", schedule); };
  }, []);

  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches || !("IntersectionObserver" in window)) return;
    const elements = root.current.querySelectorAll(".landing-intro, .story-chapter, .workflow-heading, .workflow-list li, .landing-closing");
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => { if (entry.isIntersecting) { entry.target.classList.add("is-revealed"); observer.unobserve(entry.target); } });
    }, { threshold: 0.12 });
    elements.forEach(element => { element.classList.add("scroll-reveal"); observer.observe(element); });
    return () => { observer.disconnect(); elements.forEach(element => element.classList.remove("scroll-reveal")); };
  }, []);

  function selectChapter(index) {
    setChapter(index);
    document.getElementById(`chapter-${index}`)?.scrollIntoView({ behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "instant" : "smooth", block: "center" });
  }

  return (
    <div ref={root} className={`landing-page visual-${visual} motion-${motion}`}>
      <section className="landing-hero container" aria-labelledby="landing-title">
        <div className="hero-copy">
          <p className="eyebrow">A closer look at liver health</p>
          <h1 id="landing-title">See more.<br /><span>Understand better.</span></h1>
          <p className="hero-description">Your scan. Your context.<br />A clearer place to begin the conversation.</p>
          <div className="hero-actions">
            <button className="btn btn-primary" onClick={onStart}>Start analysis <ArrowRightIcon width={18} height={18} /></button>
            <a className="quiet-link" href="#how-it-works">Take a closer look <ArrowDownIcon /></a>
          </div>
          <p className="hero-note"><InfoCircledIcon width={15} height={15} aria-hidden="true" /> <span><strong>For research and education.</strong> Not a diagnosis.</span></p>
        </div>
        {visual !== "type" && <div className="hero-object"><ScanIllustration real={real} layer={1} /></div>}
        <div className="hero-bottom"><span>Explore at your own pace <ArrowDownIcon /></span></div>
      </section>

      <section className="landing-intro container" id="how-it-works">
        <p className="eyebrow">The approach</p>
        <h2>A scan tells part of the story.<br /><span>Context brings it together.</span></h2>
        <p>Follow the image from a liver outline to exploratory measurements, then put those findings alongside the patient’s answers.</p>
      </section>

      <section className="scroll-story container" ref={story} aria-label="Explore the approach">
        <div className="story-sticky">
          <div className="story-visual"><ScanIllustration real={real} layer={chapter + 1} compact={visual === "type"} /></div>
          <div className="story-controls" aria-label="Explore each step">
            {chapters.map((item, index) => <button key={item.label} onClick={() => selectChapter(index)} aria-pressed={chapter === index}><span>0{index + 1}</span> {item.label}</button>)}
          </div>
        </div>
        <div className="story-chapters">
          {chapters.map((item, index) => <article key={item.label} id={`chapter-${index}`} className={`story-chapter ${chapter === index ? "is-current" : ""}`}>
            <p className="eyebrow">0{index + 1} / {item.label}</p>
            <h2>{item.title}</h2><p>{item.text}</p>
            {index === 1 && <span className="chapter-note">Exploratory measurements, not disease staging.</span>}
            {index === 2 && <span className="chapter-note">Illustrative projections, not a prediction of your future MRI.</span>}
          </article>)}
        </div>
      </section>

      <section className="landing-workflow container" aria-labelledby="workflow-title">
        <div className="workflow-heading"><p className="eyebrow">From scan to context</p><h2 id="workflow-title">Three steps.<br />One place to explore.</h2></div>
        <ol className="workflow-list">
          <li><span>01</span><div><h3>Bring the scan.</h3><p>Upload a ZIP with in-phase and opposed-phase DICOM images.</p></div></li>
          <li><span>02</span><div><h3>Add the context.</h3><p>Complete the short clinical questionnaire.</p></div></li>
          <li><span>03</span><div><h3>Explore the results.</h3><p>Review the scan, measurements, and questionnaire estimate together.</p></div></li>
        </ol>
      </section>

      <section className="landing-closing container">
        <p className="eyebrow">Your next step</p><h2>Begin with a closer look.</h2>
        <button className="btn btn-primary" onClick={onStart}>Start analysis <ArrowRightIcon /></button>
        <p>FibroLens supports exploration and discussion.<br />It does not replace a clinician’s evaluation.</p>
      </section>
      <footer className="landing-footer container"><span>FibroLens.</span><span>Research & education</span><a href="#landing-title">Back to top ↑</a></footer>
    </div>
  );
}
