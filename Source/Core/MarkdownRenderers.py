import json
import os

import mistune

from Core import Utility


class Renderer(mistune.Renderer):
    def __init__(self, Notebook):
        super().__init__()
        self.Notebook = Notebook

    def strikethrough(self, Text):
        return "<s>" + Text + "</s>"

    def footnote_ref(self, Key, Index):
        Key = mistune.escape(Key)
        return "<sup class=\"footnote-ref\" id=\"fnref-" + Key + "\">" + Key + "</sup>"

    def footnote_item(self, Key, Text):
        Key = mistune.escape(Key)
        Text = "<p>" + Key + ". " + Text.rstrip()[3:]
        return "<li>" + Text + "</li>\n"

    def footnotes(self, Text):
        return "<div class=\"footnotes\">\n" + self.hrule() + "<ul style=\"list-style-type:none\">" + Text + "</ul>\n</div>\n"

    def table(self, Header, Body):
        return "<p><table border=\"1\" cellpadding=\"2\">\n<thead>" + Header + "</thead>\n<tbody>\n" + Body + "</tbody>\n</table>\n"

    def header(self, text, level, raw=None):
        return "<h" + str(level) + " style=\"color: seagreen\">" + text + "</h" + str(level) + ">\n"

    def image(self, Source, Title, AltText):
        if self.Notebook.HasImage(Source):
            Source = "data:image/" + os.path.splitext(Source)[1] + ";base64, " + self.Notebook.GetImage(Source)
            AltText = mistune.escape(AltText, quote=True)
            if Title is not None:
                Title = mistune.escape(Title, quote=True)
                HTML = "<img src=\"" + Source + "\" alt=\"" + AltText + "\" title=\"" + Title + "\""
            else:
                HTML = "<img src=\"" + Source + "\" alt=\"" + AltText + "\""
            if self.options.get("use_xhtml"):
                return HTML + " />"
            return HTML + ">"
        else:
            return "IMAGE NOT FOUND|" + Source + (("|" + AltText) if AltText != "" else "") + (("|" + Title) if Title is not None and Title != "" else "")


class HTMLExportRenderer(Renderer):
    def __init__(self, Notebook):
        super().__init__(Notebook)
        self.CurrentPage = None

    def link(self, Link, Title, Text):
        if self.Notebook.StringIsValidIndexPath(Link):
            Link = self.ConstructRelativeFilePathFromIndexPathString(Link)
        Link = mistune.escape_link(Link)
        if not Title:
            return "<a href=\"" + Link + "\">" + Text + "</a>"
        Title = mistune.escape(Title, quote=True)
        return "<a href=\"" + Link + "\" title=\"" + Title + "\">" + Text + "</a>"

    def ConstructRelativeFilePathFromIndexPathString(self, IndexPathString):
        if self.CurrentPage is not None:
            # Start Relative File Path
            RelativeFilePath = ""

            # Append Relative Path to Root from Current Page
            CurrentPageIndexPath = self.CurrentPage["IndexPath"]
            RelativeFilePath += "../" * (len(CurrentPageIndexPath) - 1)

            # Append Path to Linked Page
            LinkedIndexPath = json.loads(IndexPathString)
            for IndexLevel in range(len(LinkedIndexPath)):
                CurrentLinkStepIndexPath = LinkedIndexPath[:IndexLevel + 1]
                CurrentLinkStepPage = self.Notebook.GetPageFromIndexPath(CurrentLinkStepIndexPath)
                CurrentLinkStepFileName = str(CurrentLinkStepPage["IndexPath"][-1]) + " - " + Utility.GetSafeFileNameFromPageTitle(CurrentLinkStepPage["Title"])
                RelativeFilePath += CurrentLinkStepFileName
                if IndexLevel == len(LinkedIndexPath) - 1:
                    RelativeFilePath += ".html"
                else:
                    RelativeFilePath += "/"
            return RelativeFilePath
        else:
            return IndexPathString


def ConstructMarkdownStringFromPage(Page, Notebook):
    HeaderString = Notebook.Header + "\n\n"
    HeaderString = HeaderString.replace("{PAGETITLE}", Page["Title"])
    HeaderString = HeaderString.replace("{SUBPAGELINKS}", ConstructSubPageLinks(Page))
    HeaderString = HeaderString.replace("{SUBPAGEOFLINK}", ConstructSubPageOfLink(Page, Notebook))
    FooterString = "\n\n" + Notebook.Footer
    FooterString = FooterString.replace("{PAGETITLE}", Page["Title"])
    FooterString = FooterString.replace("{SUBPAGELINKS}", ConstructSubPageLinks(Page))
    FooterString = FooterString.replace("{SUBPAGEOFLINK}", ConstructSubPageOfLink(Page, Notebook))
    MarkdownString = HeaderString + Page["Content"] + FooterString
    return MarkdownString


def ConstructSubPageLinks(Page):
    if len(Page["SubPages"]) < 1:
        LinksString = "No sub pages."
    else:
        LinksString = ""
        for SubPage in Page["SubPages"]:
            LinksString += "[" + SubPage["Title"] + "](" + json.dumps(SubPage["IndexPath"]) + ")  \n"
        LinksString = LinksString.rstrip()
    return LinksString


def ConstructSubPageOfLink(Page, Notebook):
    if Page is Notebook.RootPage:
        LinkString = "This is the root page."
    else:
        SuperPage = Notebook.GetSuperOfPageFromIndexPath(Page["IndexPath"])
        LinkString = "[" + SuperPage["Title"] + "](" + json.dumps(SuperPage["IndexPath"]) + ")"
    return LinkString