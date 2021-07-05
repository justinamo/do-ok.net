import scatter 

def append_offset(drop, offset):
    drop['offset'] = offset
    return drop

def generate():
  drops = [
    { 'name': 'learning japanese', 'link': 'https://sshh.nyc/event/class-intro-to-japanese-new-12-week-session/' }
  , { 'name': 'i/c artists webpage', 'link': '/projects#icartists' }
  , { 'name': 'personal website', 'link': '/' }
  , { 'name': 'Do Ok EP', 'link': 'https://do-ok.bandcamp.com' }
  , { 'name': 'jmail.link', 'link': 'https://jmail.link' }
  , { 'name': 'en-tranceit' }
  , ]
  
  offsets = scatter.generate(len(drops) + 1, 2)
  max_offset = max(map(abs, offsets))
  normalized_offsets = map(lambda i: i / max_offset, offsets)

  fountain_drops = list(map(append_offset, drops, normalized_offsets))
  fountain_drops.reverse()

  return fountain_drops
