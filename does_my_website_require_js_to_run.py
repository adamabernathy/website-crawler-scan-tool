import requests
from bs4 import BeautifulSoup
from requests_html import HTMLSession
import json
import base64
from sys import argv, stderr, exit
from argparse import ArgumentParser


class Helpers():
    """
    Helper Functions
    """

    def flatten_recursive(self, lst):
        # Dirty, but I got it from SO.
        # !!! Needs max loop safety before production
        flat = []
        for item in lst:
            if isinstance(item, list):
                flat.extend(self.flatten_recursive(item))
            else:
                flat.append(item)
        return flat
    
    # TODO: Move to libray if things expand
    def b64_string(self, message):
        message_bytes = message.encode('ascii')
        base64_bytes = base64.b64encode(message_bytes)
        
        return base64_bytes.decode('ascii')
    
    def save_output(self, payload, output_filename, output_format="json"):

        if output_format == "json":
            with open(output_filename, "w") as f:
                json.dump(payload, f, indent=2)


class CheckWebsiteRendering():

    def __init__(self, verbose=False, quiet=False):
        self.verbose = verbose
        self.quiet = quiet
        self.helpers = Helpers()


    """
    Private Functions
    """

    def __find_all_schema_types(self, json_data):
        """
        Recursively find all values for keys starting with '@type' in a JSON structure.
        Returns a list of found values (no duplicates).
        """
        found_types = []

        def __A(data, loop_count, max_recursion_loops):
            loop_count += 1

            if isinstance(data, dict):
                for key, value in data.items():
                    if key == '@type':
                        found_types.append(value)

                    if loop_count < max_recursion_loops:        
                        __A(value, loop_count, max_recursion_loops)

            elif isinstance(data, list):
                for item in data:
                    if loop_count < max_recursion_loops:        
                        __A(item, loop_count, max_recursion_loops)

        max_recursion_loops = 50
        loop_count = 0
        __A(json_data, loop_count, max_recursion_loops)

        return list(set(found_types))  # Remove duplicates

    """
    Public Methods
    """

    def bots_that_dont_render_js(self):
        return [
            "Bytespider", "AmazonBot", "ClaudeBot", "Meta-External Agent",
            "GPTBot", "ChatGPT-User", "PerplexityBot", "OAI-SearchBot"
        ]

    def detect_schema_types(self, url):
        try:
            r = requests.get(url, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            schema_blocks = soup.find_all("script", type="application/ld+json")

            schema_types = []

            for block in schema_blocks:
                schema_types.append(self.__find_all_schema_types(json.loads(block.string)))

            unique_types = list(set(self.helpers.flatten_recursive(schema_types)))

            return {
                "found": bool(unique_types),
                "types": unique_types or [],
                "error": False
            }

        except Exception as e:
            return {
                "found": False,
                "types": None,
                "error": f"Error: {str(e)}"
            }

    def extract_content_no_js(self, url):
        """
        Uses BS4 to parse statically returned content.
        """

        try:
            r = requests.get(url, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")

            h1_tags = [h.get_text(strip=True) for h in soup.find_all("h1")]
            h2_tags = [h.get_text(strip=True) for h in soup.find_all("h2")]
            text = soup.get_text(separator=" ", strip=True)
            word_count = len(text.split())
            char_count = len(text)

            schema = self.detect_schema_types(url)

            return {
                "h1": h1_tags,
                "h2": h2_tags,
                "word_count": word_count,
                "char_count": char_count,
                "schema": schema,
                "error": None
            }
        except Exception as e:
            return {"error": str(e), "js": False}

    def extract_content_with_js(self, url):
        """
        Locally renders the page to execute JS.
        """

        try:
            session = HTMLSession()
            r = session.get(url)
            r.html.render(timeout=20)

            h1_tags = r.html.find("h1")
            h2_tags = r.html.find("h2")
            text = r.html.full_text

            schema = self.detect_schema_types(url)

            return {
                "h1": [h.text for h in h1_tags],
                "h2": [h.text for h in h2_tags],
                "word_count": len(text.split()),
                "char_count": len(text),
                "schema": schema,
                "error": None
            }
        except Exception as e:
            return {"error": str(e), "js": True}

    def print_summary(self, label, data):
        if data.get("error"):
            print(f"\t❌ Error: {data['error']}")
            return

        # js_enabled = True if data['js'] else False
        clean_string = lambda a: a.replace("\n", " ").rstrip()
        print(f"\n{label}")

        print(f"\t{'✅' if data['h1'] else '❌'}  H1 Tags: {len(data['h1'])}x")
        if self.verbose: [print(f"\t\t- {clean_string(x)}") for x in data['h1']], print("")

        print(f"\t{'✅' if data['h2'] else '❌'}  H2 Tags: {len(data['h2'])}x")
        if self.verbose: [print(f"\t\t- {clean_string(x)}") for x in data['h2']], print("")

        try:
            print(f"\t{'✅' if data['schema']['found'] else '❌'}  Schema.org Detected: [{', '.join(data['schema']['types'])}]")
        except:
            print(data)
        
        print(f"\n\tWord Count: {data['word_count']:,}")
        print(f"\tCharacter Count: {data['char_count']:,}")

        if len(data['h1']) < 1: print(f"\n\t⚠️ Needs at least 1x H1 Tag for SEO.")

    def compare_runs(self, url, tags={}):
        completion_check = False
        print(f"\n🌐 Analyzing: {url}")
        
        page_render_with_js_disabled = self.extract_content_no_js(url)
        page_render_with_js_enabled = self.extract_content_with_js(url)

        if not self.quiet:
            self.print_summary("🟢 JavaScript Enabled", page_render_with_js_enabled)
            self.print_summary("🔘 JavaScript DISABLED", page_render_with_js_disabled)

        requires_js = None  # Set default state

        if not page_render_with_js_disabled.get("error") and not page_render_with_js_enabled.get("error"):

            word_diff = page_render_with_js_enabled["word_count"] - page_render_with_js_disabled["word_count"]
            percent_change = (word_diff / page_render_with_js_disabled["word_count"] * 100) if page_render_with_js_disabled["word_count"] else 0

            if not self.quiet:
                print(f"\n🐿️  Comparing JS vs. Non-JS Renders:")
                print(f"\tWord Count Change: {word_diff} words ({percent_change:.2f}%)")

            # This is the sauce...
            h1_tag_delta = abs(len(page_render_with_js_enabled['h1']) - len(page_render_with_js_disabled['h1'])) # Postive is bad
            h2_tag_delta = abs(len(page_render_with_js_enabled['h2']) - len(page_render_with_js_disabled['h2'])) # Postive is bad

            h1_tag_differential = h1_tag_delta / len(page_render_with_js_enabled['h1']) if len(page_render_with_js_enabled['h1']) > 0 else 1
            h2_tag_differential = h2_tag_delta / len(page_render_with_js_enabled['h2']) if len(page_render_with_js_enabled['h2']) > 0 else 1

            if not self.quiet:
                print(f"\tDelta in H1 Tags: {h1_tag_delta} ({h1_tag_differential * 100. :.2f}%)")
                print(f"\tDelta in H2 Tags: {h2_tag_delta} ({h2_tag_differential * 100. :.2f}%)")

            if sum([h1_tag_differential, h2_tag_differential]) > 0.4:
                requires_js = True

            if page_render_with_js_enabled and page_render_with_js_disabled is False:
                requires_js = True

            if requires_js is None:
                requires_js = False

            if not self.quiet:
                print(f"\n{'‼️' if requires_js else '✅'} Is JavaScript (or other page functionalty) likely required for search crawler? {'⚠️ Yes' if requires_js else '🎉 No'}")

            if requires_js:
                print(f"\nThis site is 'invisiable' to: {', '.join(self.bots_that_dont_render_js())}")


            print("\n")

            completion_check = True

        json_results = {
            "url": url,
            "js_enabled": page_render_with_js_enabled,
            "js_disabled": page_render_with_js_disabled,
            "js_required": requires_js,
            "completion_check": completion_check,
            "tags": tags,
        }
        
        # print(json.dumps(json_results, indent=2))

        return json_results


if __name__ == "__main__":

    helpers = Helpers()

    parser = ArgumentParser(
        prog='does_my_website_require_js_to_run',
        description="Is website bot friendly? I.e., does it need JavaScript to render",
        epilog="🌮s are a way of life."
    )

    parser.add_argument("--website-url", "-u", type=str, dest="website_to_check", help="Website to evaluate")
    parser.add_argument("--output", "-o", type=str, default=None, dest="output_filename", help="Save output of results")
    
    parser.add_argument("--verbose", "-v", action='store_true', default=False, dest="verbose", help="Verbose output")
    parser.add_argument("--quiet", "-q", action='store_true', default=False, dest="quiet", help="Runs quiet-er")

    if len(argv) == 1:
        parser.print_help(stderr)
        exit(1)

    args = parser.parse_args()

    checker = CheckWebsiteRendering(verbose=args.verbose, quiet=args.quiet)

    test_url = args.website_to_check
    results = checker.compare_runs(test_url)

    if args.output_filename is not None:
        helpers.save_output(results, args.output_filename)