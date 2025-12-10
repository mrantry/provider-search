# Provider Search Personas

This document defines different user personas for our provider search system. Each persona has unique priorities when searching for healthcare providers, represented by different rankings of our core values.

## Core Values

Our system evaluates providers based on five key dimensions:

1. **Convenience** - Location proximity, availability, appointment scheduling ease
2. **Shared Demographic** - Cultural background, language, age similarity
3. **Shared Values (Religion)** - Religious/spiritual alignment, values compatibility
4. **Quality** - Ratings, credentials, experience, outcomes
5. **Cost** - Price, insurance coverage, affordability

---

## Persona 1: The Busy Professional (Sarah)

**Background**: 35-year-old marketing executive, works 60+ hours/week, has good insurance

**Priority Ranking**:
1. Convenience
2. Quality
3. Cost
4. Shared Demographic
5. Shared Values (Religion)

**Description**: Sarah needs healthcare that fits into her demanding schedule. She prioritizes providers close to her office or home with evening/weekend availability. Quality matters because she wants issues resolved efficiently, but she's less concerned about cost due to comprehensive insurance. Cultural or religious alignment is not a priority.

---

## Persona 2: The Budget-Conscious Parent (Marcus)

**Background**: 42-year-old teacher, family of four, high-deductible health plan

**Priority Ranking**:
1. Cost
2. Quality
3. Convenience
4. Shared Demographic
5. Shared Values (Religion)

**Description**: Marcus is managing healthcare for his entire family on a tight budget. He needs to find affordable providers who accept his insurance and offer transparent pricing. While quality is important, he's willing to travel further or wait longer for appointments if it means significant cost savings.

---

## Persona 3: The Community-Oriented Patient (Fatima)

**Background**: 28-year-old graduate student, Muslim, moved to new city recently

**Priority Ranking**:
1. Shared Values (Religion)
2. Shared Demographic
3. Quality
4. Convenience
5. Cost

**Description**: Fatima strongly values finding providers who understand and respect her religious practices and cultural background. She wants a doctor who shares or is sensitive to her values, perhaps someone who speaks her language or understands her dietary restrictions. Finding the right cultural fit is worth extra travel time or cost.

---

## Persona 4: The Quality-First Patient (Robert)

**Background**: 58-year-old with chronic condition, retired executive, excellent insurance

**Priority Ranking**:
1. Quality
2. Shared Demographic
3. Convenience
4. Cost
5. Shared Values (Religion)

**Description**: Robert is managing a serious health condition and wants the absolute best care available. He researches credentials extensively and seeks providers with top ratings and specialized experience. He's willing to travel anywhere and pay out-of-pocket if needed. He also values providers closer to his age who might better understand his life stage.

---

## Persona 5: The Balanced Seeker (Jennifer)

**Background**: 45-year-old freelancer, moderate income, values holistic care

**Priority Ranking**:
1. Quality
2. Convenience
3. Cost
4. Shared Demographic
5. Shared Values (Religion)

**Description**: Jennifer takes a balanced approach to healthcare decisions. She wants good quality care that's reasonably convenient and affordable. She's willing to make trade-offs - traveling a bit further for better quality or paying slightly more for better ratings. She considers all factors but doesn't have extreme priorities in any single dimension.

---

## Implementation Notes

These personas will drive our re-ranking algorithm. When a user identifies with a persona (or we infer one through preferences), we'll weight the search results according to their priority ranking. For example:

- **Sarah's search** would heavily weight location/availability and ratings
- **Marcus's search** would prioritize cost-effective providers who accept his insurance
- **Fatima's search** would surface providers with matching religious/cultural backgrounds
- **Robert's search** would emphasize top-rated specialists regardless of cost
- **Jennifer's search** would use a more balanced scoring across all dimensions

The re-ranking layer will use these weighted preferences to personalize search results beyond the baseline BM25 retrieval.
