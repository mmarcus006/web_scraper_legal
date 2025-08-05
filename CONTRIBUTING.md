# Contributing to US Tax Court Document Scraper

Thank you for your interest in contributing to this project! We welcome contributions from the community.

## How to Contribute

### Reporting Issues

1. Check if the issue already exists in the [Issues](https://github.com/yourusername/web_scraper_legal/issues) section
2. If not, create a new issue with:
   - Clear description of the problem
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - System information (OS, Python version)
   - Relevant logs or error messages

### Submitting Pull Requests

1. Fork the repository
2. Create a new branch for your feature/fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Make your changes
4. Test your changes thoroughly:
   ```bash
   python run.py --help
   python run.py --stats
   python run.py --start-date 2024-12-01 --end-date 2024-12-02 --no-pdfs
   ```
5. Format your code:
   ```bash
   black dawson_scraper/src/
   ruff check dawson_scraper/src/
   ```
6. Commit your changes with a descriptive message:
   ```bash
   git commit -m "Add feature: description of your changes"
   ```
7. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
8. Create a Pull Request

### Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Add docstrings to functions and classes
- Keep functions focused and small
- Write descriptive variable names

### Testing

- Test with actual API calls (no mocks)
- Test with small date ranges to avoid excessive API usage
- Verify that existing functionality still works
- Add error handling for edge cases

### Areas for Contribution

- Performance improvements
- Additional document types support
- Export formats (CSV, Excel, etc.)
- Better error recovery mechanisms
- Documentation improvements
- Test coverage
- CLI enhancements
- Progress visualization improvements

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/web_scraper_legal.git
   cd web_scraper_legal
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install black ruff mypy pytest pytest-asyncio
   ```

3. Create a test environment:
   ```bash
   python run.py --start-date 2024-12-01 --end-date 2024-12-02 --no-pdfs
   ```

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive criticism
- Respect differing opinions

## Questions?

If you have questions, feel free to:
- Open an issue for discussion
- Check the README.md for documentation
- Review existing issues and pull requests

Thank you for contributing!