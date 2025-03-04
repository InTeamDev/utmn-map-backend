class PopularityRanker:
    def __init__(self):
        self.view_counts = {}
        self.click_counts = {}

    def update_stats(self, object_id, viewed=False, clicked=False):
        if viewed:
            self.view_counts[object_id] = self.view_counts.get(object_id, 0) + 1
        if clicked:
            self.click_counts[object_id] = self.click_counts.get(object_id, 0) + 1

    def get_popularity_score(self, object_id):
        views = self.view_counts.get(object_id, 0)
        clicks = self.click_counts.get(object_id, 0)
        return (clicks * 2 + views) / (views + 1 if views > 0 else 1)
