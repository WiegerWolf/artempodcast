import type { APIRoute } from 'astro';
import { getCollection } from 'astro:content';
import { render } from 'astro:content';

const site = 'https://artempodcast.com';
const mediaBase = 'https://media.artempodcast.com/';
const title = 'ArtemPodcast';
const authorName = 'Artem';
const authorEmail = 'u4q59hqf@tsatsin.com';
const logo = `${site}/logo.png`;

function escapeXml(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

function formatRFC822(date: Date): string {
  return date.toUTCString().replace('GMT', '+0000');
}

function stripHtml(html: string): string {
  return html.replace(/<[^>]*>/g, '').trim();
}

export const GET: APIRoute = async () => {
  const episodes = (await getCollection('episodes')).sort(
    (a, b) => b.data.date.getTime() - a.data.date.getTime()
  );

  const lastBuildDate = episodes.length > 0 ? formatRFC822(episodes[0].data.date) : formatRFC822(new Date());

  const items: string[] = [];
  for (const ep of episodes) {
    const { Content } = await render(ep);
    // We need raw HTML. Use a simple approach: render to string isn't available directly.
    // Instead, use the compiled markdown body.
    const permalink = `${site}/${ep.id}/`;
    const pubDate = formatRFC822(ep.data.date);
    const audioUrl = `${mediaBase}${ep.data.audio}`;

    // For description, use the first 200 chars of body text
    const bodyText = ep.body || '';
    const summary = escapeXml(bodyText.substring(0, 280).replace(/\n/g, ' ').trim());

    items.push(`
    <item>
      <title>${escapeXml(ep.data.title)}</title>
      <link>${permalink}</link>
      <pubDate>${pubDate}</pubDate>
      <dc:creator>${escapeXml(authorEmail)} (${escapeXml(authorName)})</dc:creator>
      <author>${escapeXml(authorEmail)} (${escapeXml(authorName)})</author>
      <guid>${permalink}</guid>
      <description>${summary}</description>
      <itunes:summary>${summary}</itunes:summary>
      <googleplay:description>${summary}</googleplay:description>
      <enclosure url="${audioUrl}" type="audio/mp3" />
    </item>`);
  }

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
  xmlns:content="http://purl.org/rss/1.0/modules/content/"
  xmlns:dc="http://purl.org/dc/elements/1.1/"
  xmlns:atom="http://www.w3.org/2005/Atom"
  xmlns:sy="http://purl.org/rss/1.0/modules/syndication/"
  xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"
  xmlns:googleplay="http://www.google.com/schemas/play-podcasts/1.0"
>
  <channel>
    <title>${escapeXml(title)}</title>
    <link>${site}</link>
    <description>Recent content on ${escapeXml(title)}</description>
    <language>ru-ru</language>
    <lastBuildDate>${lastBuildDate}</lastBuildDate>
    <sy:updatePeriod>hourly</sy:updatePeriod>
    <sy:updateFrequency>1</sy:updateFrequency>
    <atom:link href="${site}/index.xml" rel="self" type="application/rss+xml" />
    <googleplay:email>${escapeXml(authorEmail)}</googleplay:email>
    <webMaster>${escapeXml(authorEmail)} (${escapeXml(authorName)})</webMaster>
    <managingEditor>${escapeXml(authorEmail)} (${escapeXml(authorName)})</managingEditor>
    <itunes:owner>
      <itunes:name>${escapeXml(authorName)}</itunes:name>
      <itunes:email>${escapeXml(authorEmail)}</itunes:email>
    </itunes:owner>
    <googleplay:author>${escapeXml(authorName)}</googleplay:author>
    <itunes:author>${escapeXml(authorName)}</itunes:author>
    <itunes:summary>Recent content on ${escapeXml(title)}</itunes:summary>
    <googleplay:description>Recent content on ${escapeXml(title)}</googleplay:description>
    <itunes:explicit>no</itunes:explicit>
    <itunes:category text="Technology" />
    <itunes:image href="${logo}" />
    <googleplay:image href="${logo}" />
    <image>
      <url>${logo}</url>
      <title>${escapeXml(title)}</title>
      <link>${site}</link>
    </image>
${items.join('\n')}
  </channel>
</rss>`;

  return new Response(xml, {
    headers: {
      'Content-Type': 'application/xml; charset=utf-8',
    },
  });
};
