# Runtime

For v0.1, the compiler generates a self-contained HTML file with embedded CSS and minimal JavaScript only when required. Anzer should not require a custom browser runtime for these initial pages. This is a compatibility milestone, not Anzer's long-term vision of replacing HTML as the author-facing language.

If runtime helpers become necessary, they should be small, documented, versioned, and avoid unnecessary dependencies.
